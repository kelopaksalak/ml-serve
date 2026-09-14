import joblib
import numpy as np
from sklearn.linear_model import LinearRegression

X = np.array([[1, 2], [3, 4], [5, 6], [7, 8], [9, 10]])
y = np.array([3, 7, 11, 15, 19])

model = LinearRegression()
model.fit(X, y)
model.feature_names_in_ = np.array(["feature1", "feature2"])

joblib.dump(model, "fake_model.pkl")
print("Created test_model/fake_model.pkl")
print("Features: feature1, feature2")
print("Try: predict [2, 3] -> should be ~5")
