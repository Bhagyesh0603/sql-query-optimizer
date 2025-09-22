import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split, cross_val_score
import joblib
import json
from typing import Dict, List, Tuple, Any
from ml_optimizer.feature_extraction import extract_features

class AdvancedMLOptimizer:
    """Advanced ML-based query optimization with multiple models and ensemble learning"""
    
    def __init__(self):
        self.models = {}
        self.ensemble_weights = {}
        self.feature_importance = {}
        self.model_performance = {}
        
    def train_ensemble_models(self, queries: List[str], actual_costs: List[float], 
                            features_data: List[Dict] = None) -> Dict[str, Any]:
        """Train multiple models and create ensemble"""
        
        # Extract features if not provided
        if features_data is None:
            features_data = [extract_features(query) for query in queries]
        
        # Convert to DataFrame
        df = pd.DataFrame(features_data)
        
        # Select most important features (you can expand this list)
        important_features = [
            'num_tables', 'num_joins', 'query_length', 'num_conditions', 
            'query_complexity', 'has_order_by', 'num_aggregates', 'has_subquery',
            'has_union', 'max_nesting_depth'
        ]
        
        # Ensure we have these features
        for feature in important_features:
            if feature not in df.columns:
                df[feature] = 0
        
        X = df[important_features].fillna(0)
        y = np.array(actual_costs)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Define models to train
        model_configs = {
            'random_forest': RandomForestRegressor(
                n_estimators=100, 
                max_depth=10, 
                min_samples_split=5,
                random_state=42
            ),
            'gradient_boosting': GradientBoostingRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            ),
            'linear_regression': LinearRegression()
        }
        
        results = {
            'model_performance': {},
            'feature_importance': {},
            'ensemble_weights': {},
            'training_metrics': {}
        }
        
        # Train each model
        model_predictions = {}
        
        for name, model in model_configs.items():
            print(f"Training {name}...")
            
            # Train model
            model.fit(X_train, y_train)
            
            # Make predictions
            train_pred = model.predict(X_train)
            test_pred = model.predict(X_test)
            
            # Calculate metrics
            train_mae = mean_absolute_error(y_train, train_pred)
            test_mae = mean_absolute_error(y_test, test_pred)
            train_r2 = r2_score(y_train, train_pred)
            test_r2 = r2_score(y_test, test_pred)
            
            # Cross-validation score
            cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='neg_mean_absolute_error')
            cv_mae = -cv_scores.mean()
            
            # Store model and metrics
            self.models[name] = model
            model_predictions[name] = test_pred
            
            performance = {
                'train_mae': train_mae,
                'test_mae': test_mae, 
                'train_r2': train_r2,
                'test_r2': test_r2,
                'cv_mae': cv_mae,
                'cv_std': cv_scores.std()
            }
            
            results['model_performance'][name] = performance
            self.model_performance[name] = performance
            
            # Feature importance (if available)
            if hasattr(model, 'feature_importances_'):
                importance_dict = dict(zip(important_features, model.feature_importances_))
                results['feature_importance'][name] = importance_dict
                self.feature_importance[name] = importance_dict
            
            print(f"  {name}: Test MAE={test_mae:.3f}, Test R²={test_r2:.3f}, CV MAE={cv_mae:.3f}")
        
        # Calculate ensemble weights based on performance (inverse of error)
        test_errors = {name: perf['test_mae'] for name, perf in results['model_performance'].items()}
        
        # Weights inversely proportional to error (better models get higher weight)
        inv_errors = {name: 1.0 / (error + 0.001) for name, error in test_errors.items()}
        total_inv_error = sum(inv_errors.values())
        weights = {name: inv_error / total_inv_error for name, inv_error in inv_errors.items()}
        
        self.ensemble_weights = weights
        results['ensemble_weights'] = weights
        
        # Test ensemble performance
        ensemble_pred = self._ensemble_predict(X_test, weights)
        ensemble_mae = mean_absolute_error(y_test, ensemble_pred)
        ensemble_r2 = r2_score(y_test, ensemble_pred)
        
        results['model_performance']['ensemble'] = {
            'test_mae': ensemble_mae,
            'test_r2': ensemble_r2
        }
        
        print(f"Ensemble: Test MAE={ensemble_mae:.3f}, Test R²={ensemble_r2:.3f}")
        
        # Store training data for model updates
        results['training_metrics'] = {
            'num_samples': len(queries),
            'num_features': len(important_features),
            'feature_names': important_features,
            'best_single_model': min(test_errors.keys(), key=lambda x: test_errors[x])
        }
        
        return results
    
    def _ensemble_predict(self, X: pd.DataFrame, weights: Dict[str, float] = None) -> np.ndarray:
        """Make ensemble predictions"""
        if weights is None:
            weights = self.ensemble_weights
        
        predictions = []
        total_weight = 0
        
        for name, model in self.models.items():
            if name in weights:
                pred = model.predict(X)
                weight = weights[name]
                predictions.append(pred * weight)
                total_weight += weight
        
        if total_weight == 0:
            # Fallback to equal weights
            return np.mean([model.predict(X) for model in self.models.values()], axis=0)
        
        return np.sum(predictions, axis=0) / total_weight
    
    def predict_cost(self, query: str, use_ensemble: bool = True) -> Dict[str, float]:
        """Predict query cost using trained models"""
        features = extract_features(query)
        
        # Prepare feature vector
        important_features = [
            'num_tables', 'num_joins', 'query_length', 'num_conditions',
            'query_complexity', 'has_order_by', 'num_aggregates', 'has_subquery',
            'has_union', 'max_nesting_depth'
        ]
        
        feature_vector = [features.get(f, 0) for f in important_features]
        X = pd.DataFrame([feature_vector], columns=important_features)
        
        predictions = {}
        
        # Individual model predictions
        for name, model in self.models.items():
            try:
                pred = model.predict(X)[0]
                predictions[f'{name}_prediction'] = pred
            except Exception as e:
                print(f"Error predicting with {name}: {e}")
                predictions[f'{name}_prediction'] = None
        
        # Ensemble prediction
        if use_ensemble and self.ensemble_weights:
            try:
                ensemble_pred = self._ensemble_predict(X)[0]
                predictions['ensemble_prediction'] = ensemble_pred
                predictions['recommended_prediction'] = ensemble_pred
            except Exception as e:
                print(f"Error with ensemble prediction: {e}")
                predictions['recommended_prediction'] = predictions.get('random_forest_prediction', 0.5)
        else:
            predictions['recommended_prediction'] = predictions.get('random_forest_prediction', 0.5)
        
        # Add confidence metrics
        individual_preds = [v for k, v in predictions.items() 
                          if k.endswith('_prediction') and k != 'ensemble_prediction' and v is not None]
        
        if len(individual_preds) > 1:
            predictions['prediction_std'] = np.std(individual_preds)
            predictions['prediction_variance'] = np.var(individual_preds)
            predictions['confidence'] = max(0, 1 - (np.std(individual_preds) / np.mean(individual_preds)))
        
        return predictions
    
    def save_models(self, filepath: str):
        """Save all trained models"""
        model_data = {
            'models': self.models,
            'ensemble_weights': self.ensemble_weights,
            'feature_importance': self.feature_importance,
            'model_performance': self.model_performance,
            'version': '2.0',
            'features': [
                'num_tables', 'num_joins', 'query_length', 'num_conditions',
                'query_complexity', 'has_order_by', 'num_aggregates', 'has_subquery',
                'has_union', 'max_nesting_depth'
            ]
        }
        
        joblib.dump(model_data, filepath)
        print(f"Advanced models saved to {filepath}")
    
    def load_models(self, filepath: str):
        """Load trained models"""
        try:
            model_data = joblib.load(filepath)
            self.models = model_data['models']
            self.ensemble_weights = model_data.get('ensemble_weights', {})
            self.feature_importance = model_data.get('feature_importance', {})
            self.model_performance = model_data.get('model_performance', {})
            print(f"Advanced models loaded from {filepath}")
            return True
        except Exception as e:
            print(f"Error loading models: {e}")
            return False
    
    def generate_model_report(self) -> str:
        """Generate detailed model performance report"""
        if not self.model_performance:
            return "No trained models available"
        
        report = []
        report.append("🤖 ADVANCED ML MODEL REPORT")
        report.append("=" * 50)
        
        # Model performance comparison
        report.append("\n📊 MODEL PERFORMANCE COMPARISON:")
        report.append("-" * 40)
        
        for name, perf in self.model_performance.items():
            if name == 'ensemble':
                continue
                
            report.append(f"\n{name.replace('_', ' ').title()}:")
            report.append(f"  • Test MAE: {perf['test_mae']:.3f}")
            report.append(f"  • Test R²: {perf['test_r2']:.3f}")
            report.append(f"  • CV MAE: {perf['cv_mae']:.3f} ± {perf['cv_std']:.3f}")
        
        # Ensemble performance
        if 'ensemble' in self.model_performance:
            ens_perf = self.model_performance['ensemble']
            report.append(f"\n🎯 Ensemble Model:")
            report.append(f"  • Test MAE: {ens_perf['test_mae']:.3f}")
            report.append(f"  • Test R²: {ens_perf['test_r2']:.3f}")
        
        # Feature importance
        if self.feature_importance:
            report.append(f"\n🔍 FEATURE IMPORTANCE (Random Forest):")
            report.append("-" * 40)
            
            if 'random_forest' in self.feature_importance:
                rf_importance = self.feature_importance['random_forest']
                sorted_features = sorted(rf_importance.items(), key=lambda x: x[1], reverse=True)
                
                for feature, importance in sorted_features[:10]:  # Top 10
                    bar = "█" * int(importance * 50)  # Visual bar
                    report.append(f"  {feature:20} {importance:.3f} {bar}")
        
        # Ensemble weights
        if self.ensemble_weights:
            report.append(f"\n⚖️ ENSEMBLE WEIGHTS:")
            report.append("-" * 20)
            for name, weight in self.ensemble_weights.items():
                report.append(f"  {name:15} {weight:.3f}")
        
        return "\n".join(report)

def train_advanced_models_from_logs():
    """Train advanced models from query logs"""
    from query_logger import get_logged_queries
    
    # Get training data from logs
    queries, costs, features = get_logged_queries()
    
    if len(queries) < 10:
        print("⚠️ Not enough training data. Need at least 10 queries.")
        return None
    
    # Initialize and train
    optimizer = AdvancedMLOptimizer()
    results = optimizer.train_ensemble_models(queries, costs, features)
    
    # Save models
    optimizer.save_models("advanced_cost_predictor.joblib")
    
    print("\n" + optimizer.generate_model_report())
    
    return optimizer