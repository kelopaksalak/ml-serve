import json
from pathlib import Path

import joblib
from sklearn.base import is_regressor
from flask import current_app
from sqlalchemy.exc import IntegrityError

from app.database import db
from app.models.ml_model import MLModel


class MlModelService:
    MODELS_DIR = (
        Path(__file__).resolve().parents[2] / "ml_models"
    )

    def get_all(self):
        return MLModel.query.all()

    def get_by_id(self, id):
        return db.session.get(MLModel, id)

    def create(self, data):
        if MLModel.query.filter_by(name=data["name"]).first():
            return None, "Model already registered"

        model_path = (
            self.MODELS_DIR / f"{data['name']}.pkl"
        ).resolve()

        if model_path.parent != self.MODELS_DIR.resolve():
            return None, "Invalid model name"

        if not model_path.is_file():
            return None, "Model file not found in ml_models/"

        try:
            ml = joblib.load(model_path)
        except Exception:
            current_app.logger.exception("Model loading failed")
            return None, "Could not load model file"

        if not callable(getattr(ml, "predict", None)):
            return None, "Model does not support prediction"

        features = getattr(ml, "feature_names_in_", None)
        feature_names = (
            [str(name) for name in features]
            if features is not None
            else []
        )

        model = MLModel(
            name=data["name"],
            description=data.get("description", ""),
            model_type=data.get(
                "model_type", "regressor" if is_regressor(ml) else "classifier"
            ),
            features=json.dumps(feature_names),
            model_path=str(model_path),
        )

        db.session.add(model)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return None, "Could not register model; check model name"

        return model, None

    def predict(self, id, features):
        model = self.get_by_id(id)

        if model is None:
            return None, "Model not found"

        try:
            ml = joblib.load(model.model_path)
        except Exception:
            current_app.logger.exception("Model loading failed")
            return None, "Could not load model file"

        expected_count = getattr(ml, "n_features_in_", None)

        if (
            expected_count is not None
            and len(features) != expected_count
        ):
            return None, (
                f"Expected {expected_count} features, "
                f"received {len(features)}"
            )

        try:
            prediction = ml.predict([features])
            result = prediction[0]

            if hasattr(result, "tolist"):
                result = result.tolist()

            return {"prediction": result}, None
        except Exception:
            current_app.logger.exception("Prediction failed")
            return None, "Prediction failed; check model and features"
