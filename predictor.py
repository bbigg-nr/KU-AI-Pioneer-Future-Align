"""
predictor.py
------------
CareerSuccessPredictor — train จาก alumni outcome data
แล้ว predict ว่านิสิตจะประสบความสำเร็จแค่ไหนในแต่ละอาชีพ (PyTorch)

Features (9 total):
  match_score       — cosine-based skill match (0–1)
  matched_count     — จำนวน tech skills ที่ match ได้
  missing_count     — จำนวน skills ที่ขาด
  gpa               — GPA ของนิสิต (0–4)
  core_gpa          — เกรดเฉลี่ยเฉพาะวิชาแกน (0–4)
  faculty_onehot    — one-hot encoding ของ faculty (OOV = all zeros)
  coverage_ratio    — matched / (matched + missing), coverage of job requirements
  avg_skill_level   — normalized average student skill level (0–1)

Target (composite):
  0.7 × (success_score / 99) + 0.3 × (1 / log1p(years_to_promotion))
"""

from __future__ import annotations
import math
import os
import copy
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader

MODEL_PATH = os.getenv("PREDICTOR_MODEL_PATH", "./predictor_model.pt")

KNOWN_FACULTIES = ["Computer Engineering", "Economics"]
NUM_FACULTIES = len(KNOWN_FACULTIES)
INPUT_DIM = 5 + NUM_FACULTIES + 2  # 5 numeric + one-hot faculty + coverage_ratio + avg_skill_level

GRADE_MAP = {"A": 4.0, "B+": 3.5, "B": 3.0, "C+": 2.5, "C": 2.0, "D+": 1.5, "D": 1.0, "F": 0.0}


def calculate_core_gpa(courses: list[dict]) -> float:
    if not courses:
        return 0.0
    total = sum(GRADE_MAP.get(c.get("grade", ""), 0.0) for c in courses)
    return total / len(courses)


def _encode_faculty(faculty: str) -> list[float]:
    """One-hot encoding — OOV (unknown faculty) = all zeros."""
    vec = [0.0] * NUM_FACULTIES
    idx = next((i for i, f in enumerate(KNOWN_FACULTIES) if f == faculty), None)
    if idx is not None:
        vec[idx] = 1.0
    return vec


class SuccessPredictorNN(nn.Module):
    def __init__(self, input_dim: int = INPUT_DIM):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.BatchNorm1d(32),
            nn.Dropout(0.2),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        return self.net(x).squeeze(-1)


class CareerSuccessPredictor:
    def __init__(self) -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = SuccessPredictorNN(input_dim=INPUT_DIM).to(self.device)
        self.is_fitted = False
        self.training_size = 0
        # Platt scaling params (4.2): calibrated = sigmoid(platt_a * raw + platt_b)
        self.platt_a: float = 1.0
        self.platt_b: float = 0.0
        self.platt_fitted: bool = False

    def _build_features(
        self,
        match_score: float,
        matched_count: int,
        missing_count: int,
        gpa: float,
        core_gpa: float,
        faculty: str,
        coverage_ratio: float | None = None,
        avg_skill_level: float | None = None,
    ) -> list[float]:
        total = matched_count + missing_count
        cov = coverage_ratio if coverage_ratio is not None else (matched_count / total if total > 0 else 0.0)
        asl = avg_skill_level if avg_skill_level is not None else 0.5
        return [
            float(match_score),
            float(matched_count),
            float(missing_count),
            float(gpa),
            float(core_gpa),
            *_encode_faculty(faculty),
            float(cov),
            float(asl),
        ]

    def train(
        self,
        records: list[dict],
        epochs: int = 300,
        batch_size: int = 16,
        patience: int = 20,
    ) -> None:
        """
        records: list ของ dict แต่ละตัวมี:
          match_score, matched_count, missing_count, gpa, core_gpa, faculty,
          success_score (0–99), years_to_promotion (int >= 1),
          coverage_ratio (optional), avg_skill_level (optional)
        """
        X, y = [], []
        for r in records:
            X.append(self._build_features(
                r["match_score"], r["matched_count"], r["missing_count"],
                r["gpa"], r["core_gpa"], r["faculty"],
                r.get("coverage_ratio"), r.get("avg_skill_level"),
            ))
            # 5.2: log1p scale prevents cliff between years_to_promotion=1 and =5
            promotion_score = 1.0 / math.log1p(max(r["years_to_promotion"], 1))
            target = (r["success_score"] / 99.0) * 0.7 + promotion_score * 0.3
            y.append(float(target))

        if not X:
            print("No records to train.")
            return

        X_tensor = torch.tensor(X, dtype=torch.float32).to(self.device)
        y_tensor = torch.tensor(y, dtype=torch.float32).to(self.device)

        # Early stopping: split 80/20 only when enough data
        use_val = len(X) >= 10
        if use_val:
            split = max(1, int(0.8 * len(X)))
            X_train, X_val = X_tensor[:split], X_tensor[split:]
            y_train, y_val = y_tensor[:split], y_tensor[split:]
        else:
            X_train, y_train = X_tensor, y_tensor
            X_val, y_val = X_tensor, y_tensor  # overfit small set

        dataset = TensorDataset(X_train, y_train)
        effective_batch = min(batch_size, len(X_train))
        dataloader = DataLoader(dataset, batch_size=effective_batch, shuffle=True)

        criterion = nn.MSELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=0.005, weight_decay=1e-4)

        best_val_loss = float("inf")
        no_improve = 0
        best_state: dict | None = None

        for epoch in range(epochs):
            self.model.train()
            for batch_X, batch_y in dataloader:
                if batch_X.size(0) <= 1:
                    continue
                optimizer.zero_grad()
                loss = criterion(self.model(batch_X), batch_y)
                loss.backward()
                optimizer.step()

            # Validation check for early stopping
            self.model.eval()
            with torch.no_grad():
                val_loss = criterion(self.model(X_val), y_val).item()

            if val_loss < best_val_loss - 1e-4:
                best_val_loss = val_loss
                best_state = copy.deepcopy(self.model.state_dict())
                no_improve = 0
            else:
                no_improve += 1
                if use_val and no_improve >= patience:
                    print(f"  Early stopping at epoch {epoch + 1} (val_loss={best_val_loss:.5f})")
                    break

        if best_state is not None:
            self.model.load_state_dict(best_state)

        self.is_fitted = True
        self.training_size = len(records)

        torch.save({
            "state_dict":    self.model.state_dict(),
            "is_fitted":     self.is_fitted,
            "input_dim":     INPUT_DIM,
            "training_size": self.training_size,
            "platt_a":       self.platt_a,
            "platt_b":       self.platt_b,
            "platt_fitted":  self.platt_fitted,
        }, MODEL_PATH)
        print(f"Predictor trained on {len(records)} records -> {MODEL_PATH}")

    def calibrate(self, raw_scores: list[float], binary_outcomes: list[int]) -> None:
        """4.2 Platt Scaling: fit sigmoid on (raw_score → binary outcome) backtest data.
        binary_outcomes: 1 = นิสิตได้งาน/ประสบความสำเร็จ, 0 = ไม่
        """
        if len(raw_scores) < 5:
            print("Too few samples for Platt calibration (need >= 5)")
            return

        scores_t = torch.tensor(raw_scores, dtype=torch.float32)
        labels_t = torch.tensor(binary_outcomes, dtype=torch.float32)

        a = nn.Parameter(torch.ones(1))
        b = nn.Parameter(torch.zeros(1))
        opt = optim.LBFGS([a, b], lr=0.1, max_iter=100)
        bce = nn.BCEWithLogitsLoss()

        def closure():
            opt.zero_grad()
            logits = a * scores_t + b
            loss = bce(logits, labels_t)
            loss.backward()
            return loss

        opt.step(closure)

        self.platt_a = float(a.detach())
        self.platt_b = float(b.detach())
        self.platt_fitted = True
        print(f"Platt calibration fitted: a={self.platt_a:.4f}, b={self.platt_b:.4f}")

    def predict(
        self,
        match_score: float,
        matched_count: int,
        missing_count: int,
        gpa: float,
        core_gpa: float,
        faculty: str,
        coverage_ratio: float | None = None,
        avg_skill_level: float | None = None,
    ) -> float:
        if not self.is_fitted:
            return 0.0

        self.model.eval()
        feat = self._build_features(
            match_score, matched_count, missing_count,
            gpa, core_gpa, faculty, coverage_ratio, avg_skill_level,
        )
        with torch.no_grad():
            raw = self.model(torch.tensor([feat], dtype=torch.float32).to(self.device)).item()

        if self.platt_fitted:
            raw = float(torch.sigmoid(torch.tensor(self.platt_a * raw + self.platt_b)).item())

        return float(max(0.0, min(raw, 1.0)))

    @classmethod
    def load(cls) -> "CareerSuccessPredictor":
        instance = cls()
        if os.path.exists(MODEL_PATH):
            try:
                ckpt = torch.load(MODEL_PATH, map_location=instance.device, weights_only=False)
                saved_dim = ckpt.get("input_dim", INPUT_DIM)
                if saved_dim != INPUT_DIM:
                    print(f"WARNING: saved model input_dim={saved_dim} != current INPUT_DIM={INPUT_DIM}. Retrain required.")
                else:
                    instance.model = SuccessPredictorNN(input_dim=saved_dim).to(instance.device)
                    instance.model.load_state_dict(ckpt["state_dict"])
                    instance.is_fitted = ckpt.get("is_fitted", True)
                    instance.training_size = ckpt.get("training_size", 0)
                    instance.platt_a = ckpt.get("platt_a", 1.0)
                    instance.platt_b = ckpt.get("platt_b", 0.0)
                    instance.platt_fitted = ckpt.get("platt_fitted", False)
            except Exception as e:
                print(f"Failed to load predictor from {MODEL_PATH}: {e}")
        return instance
