"""
Tests scikit-learn's binarizer converter.
"""
import unittest
import numpy
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.datasets import load_iris
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from skl2onnx.common.data_types import FloatTensorType
from skl2onnx import convert_sklearn, update_registered_converter
from skl2onnx.common.shape_calculator import calculate_linear_classifier_output_shapes
from skl2onnx.operator_converters.LinearClassifier import convert_sklearn_linear_classifier
from test_utils import dump_data_and_model


class MyCustomClassifier(BaseEstimator, ClassifierMixin):
    "does a simple logistic regression"
    def __init__(self, penalty='l1'):
        BaseEstimator.__init__(self)
        ClassifierMixin.__init__(self)
        self.penalty = penalty
        self.estimator = LogisticRegression(penalty=self.penalty)
    def fit(self, X, y, sample_weight=None):
        self.estimator_ = self.estimator.fit(X, y, sample_weight=sample_weight)
        return self
    def predict(self, X):
        return self.estimator_.predict(X)
    def predict_proba(self, X):
        return self.estimator_.predict_proba(X)
    def decision_function(self, X):
        return self.estimator_.decision_function(X)
        
        
def my_custom_shape_extractor(operator):
    raw = operator.raw_operator
    operator.raw_operator = raw.estimator_
    calculate_linear_classifier_output_shapes(operator)
    operator.raw_operator = raw


def my_custom_converter(scope, operator, container):
    raw = operator.raw_operator
    operator.raw_operator = raw.estimator_
    convert_sklearn_linear_classifier(scope, operator, container)
    operator.raw_operator = raw


class TestOtherLibrariesInPipeline(unittest.TestCase):

    def test_custom_pipeline_scaler(self):
        update_registered_converter(MyCustomClassifier, 'MyCustomClassifier',                                    
                                    my_custom_shape_extractor, my_custom_converter)
        
        data = load_iris()
        X = data.data[:, :2]
        y = data.target
        
        model = MyCustomClassifier()
        pipe = Pipeline([('scaler', StandardScaler()), ('lgbm', model)])
        pipe.fit(X, y)

        model_onnx = convert_sklearn(pipe, 'pipeline', [('input', FloatTensorType([1, 2]))])
        self.assertTrue(model_onnx is not None)
        dump_data_and_model(X.astype(numpy.float32), pipe, model_onnx,
                            basename="SklearnPipelineScalerCustomClassifier")

        

if __name__ == "__main__":
    unittest.main()