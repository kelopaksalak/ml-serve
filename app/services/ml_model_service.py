import os
import json
import joblib
from app.models.ml_model import MLModel
from app.database import db

class MlModelService:
    MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'ml_models')

    # get all models
    def get_all(self):
        return MLModel.query.all()

    # get model by id
    def get_by_id(self, id):
        return MLModel.query.get(id)

    # save model in db
    def create(self, data, created_by):
        model_path = os.path.join(self.MODELS_DIR, f"{data['name']}.pkl")
        if not os.path.exists(model_path):
            return None, 'Model file not found in ml_models/'

        ml = joblib.load(model_path)
        features = getattr(ml, 'feature_names_in_', None)

        model = MLModel(
            name = data['name'],
            description = data.get('description', ''),
            model_type = data.get('model_type', 'classifier'),
            features = json.dump(list(features)) if features is not None else '[]',
            model_path = model_path,
            created_by = created_by
        )

        db.session.add(model)
        db.session.commit()
        return model, None

    def predict(self, id, features):
        model = MLModel.query.get(id)
        if not model:
            return None, 'Model not found'

        ml = joblib.load(model.model_path)
        prediction = ml.predict([features])
        result = prediction[0]

        if hasattr(result, 'tolist'):
            result = result.tolist()

        return {'prediction': result}, None

    