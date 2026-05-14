"""
F1 Strategy Platform v6.0 - Schema Validation
Validates all incoming data against defined schemas.
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pydantic import BaseModel, validator, ValidationError as PydanticValidationError
import pandas as pd


@dataclass
class ValidationResult:
    """Result of data validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    data_quality_score: float  # 0-100
    cleaned_data: Optional[Any] = None


class SimulationRequestSchema(BaseModel):
    """Schema for simulation requests."""
    circuit: str
    laps: Optional[int] = None
    strategy_type: str = "auto"
    tire_compound: str = "soft"
    weather: str = "dry"
    include_safety_car: bool = False
    
    @validator('circuit')
    def validate_circuit(cls, v):
        valid_circuits = ['Monza', 'Silverstone', 'Spa', 'Monaco', 'Suzuka', 
                         'Red Bull Ring', 'Hungaroring', 'Catalunya']
        if v not in valid_circuits:
            raise ValueError(f'Invalid circuit: {v}')
        return v
    
    @validator('strategy_type')
    def validate_strategy(cls, v):
        if v not in ['auto', '1_stop', '2_stop', '3_stop']:
            raise ValueError(f'Invalid strategy type: {v}')
        return v
    
    @validator('weather')
    def validate_weather(cls, v):
        if v not in ['dry', 'wet', 'mixed']:
            raise ValueError(f'Invalid weather: {v}')
        return v


class LapDataSchema(BaseModel):
    """Schema for lap telemetry data."""
    lap_number: int
    lap_time: float
    tire_age: int
    tire_compound: str
    fuel_load: float
    
    @validator('lap_number')
    def validate_lap(cls, v):
        if v < 1 or v > 100:
            raise ValueError('Lap number must be between 1 and 100')
        return v
    
    @validator('lap_time')
    def validate_time(cls, v):
        if v < 50 or v > 300:
            raise ValueError('Lap time unrealistic (must be 50-300s)')
        return v
    
    @validator('tire_age')
    def validate_tire_age(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Tire age must be 0-100 laps')
        return v


class StrategyResultSchema(BaseModel):
    """Schema for strategy results."""
    best_strategy: str
    total_time: float
    pit_laps: List[int]
    tires_used: List[str]
    
    @validator('total_time')
    def validate_time(cls, v):
        if v <= 0 or v > 10000:
            raise ValueError('Total time must be realistic')
        return v
    
    @validator('pit_laps')
    def validate_pits(cls, v):
        if len(v) > 5:
            raise ValueError('More than 5 pit stops is unrealistic')
        return v


class SchemaValidator:
    """
    Central schema validation for all system data.
    
    Ensures:
    - Data format compliance
    - Value ranges
    - Referential integrity
    - Business rule validation
    """
    
    SCHEMAS = {
        'simulation_request': SimulationRequestSchema,
        'lap_data': LapDataSchema,
        'strategy_result': StrategyResultSchema
    }
    
    @staticmethod
    def validate(data: Dict, schema_name: str) -> ValidationResult:
        """
        Validate data against a schema.
        
        Args:
            data: Data to validate
            schema_name: Name of schema to use
        
        Returns:
            ValidationResult with details
        """
        if schema_name not in SchemaValidator.SCHEMAS:
            return ValidationResult(
                is_valid=False,
                errors=[f"Unknown schema: {schema_name}"],
                warnings=[],
                data_quality_score=0
            )
        
        schema_class = SchemaValidator.SCHEMAS[schema_name]
        
        try:
            validated = schema_class(**data)
            return ValidationResult(
                is_valid=True,
                errors=[],
                warnings=[],
                data_quality_score=100,
                cleaned_data=validated.dict()
            )
        except PydanticValidationError as e:
            errors = []
            warnings = []
            
            for error in e.errors():
                field = " -> ".join(str(x) for x in error['loc'])
                msg = error['msg']
                
                if error['type'] == 'value_error':
                    errors.append(f"{field}: {msg}")
                else:
                    warnings.append(f"{field}: {msg}")
            
            # Calculate quality score based on error severity
            score = max(0, 100 - len(errors) * 20 - len(warnings) * 5)
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                data_quality_score=score
            )
    
    @staticmethod
    def validate_dataframe(df: pd.DataFrame, expected_columns: List[str], 
                          numeric_ranges: Dict[str, tuple] = None) -> ValidationResult:
        """
        Validate a pandas DataFrame.
        
        Args:
            df: DataFrame to validate
            expected_columns: Required columns
            numeric_ranges: {column: (min, max)} for numeric validation
        
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        
        # Check missing columns
        missing = set(expected_columns) - set(df.columns)
        if missing:
            errors.append(f"Missing columns: {missing}")
        
        # Check for nulls
        null_counts = df.isnull().sum()
        high_null_cols = null_counts[null_counts > len(df) * 0.1].index.tolist()
        if high_null_cols:
            warnings.append(f"High null ratio (>10%) in: {high_null_cols}")
        
        # Check numeric ranges
        if numeric_ranges:
            for col, (min_val, max_val) in numeric_ranges.items():
                if col in df.columns:
                    out_of_range = df[(df[col] < min_val) | (df[col] > max_val)]
                    if len(out_of_range) > 0:
                        pct = len(out_of_range) / len(df) * 100
                        if pct > 5:
                            errors.append(f"{col}: {pct:.1f}% values out of range [{min_val}, {max_val}]")
                        else:
                            warnings.append(f"{col}: {pct:.1f}% values out of range")
        
        # Calculate quality score
        score = 100
        score -= len(errors) * 15
        score -= len(warnings) * 5
        score -= (null_counts.sum() / (len(df) * len(df.columns))) * 20
        score = max(0, score)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            data_quality_score=score,
            cleaned_data=df if len(errors) == 0 else None
        )
    
    @staticmethod
    def sanitize_input(value: Any, max_length: int = 1000) -> Any:
        """
        Sanitize input to prevent injection attacks.
        
        Args:
            value: Input value
            max_length: Maximum string length
        
        Returns:
            Sanitized value
        """
        if isinstance(value, str):
            # Remove null bytes
            value = value.replace('\x00', '')
            # Truncate if too long
            if len(value) > max_length:
                value = value[:max_length]
            # Strip dangerous characters for SQL
            dangerous = ['--', '/*', '*/', ';', 'DROP', 'DELETE']
            for d in dangerous:
                value = value.replace(d, '')
            return value.strip()
        
        elif isinstance(value, dict):
            return {k: SchemaValidator.sanitize_input(v, max_length) 
                   for k, v in value.items()}
        
        elif isinstance(value, list):
            return [SchemaValidator.sanitize_input(v, max_length) for v in value]
        
        return value


if __name__ == "__main__":
    # Test validation
    print("Testing Schema Validator")
    print("=" * 60)
    
    # Valid data
    valid_data = {
        "circuit": "Monza",
        "strategy_type": "2_stop",
        "weather": "dry"
    }
    result = SchemaValidator.validate(valid_data, "simulation_request")
    print(f"✓ Valid data: score={result.data_quality_score}%")
    
    # Invalid data
    invalid_data = {
        "circuit": "InvalidCircuit",
        "strategy_type": "10_stop",  # Invalid
        "weather": "sunny"  # Invalid
    }
    result = SchemaValidator.validate(invalid_data, "simulation_request")
    print(f"✗ Invalid data: {len(result.errors)} errors, score={result.data_quality_score}%")
    for err in result.errors:
        print(f"  - {err}")
    
    # Test DataFrame validation
    df = pd.DataFrame({
        'lap_time': [85.5, 86.2, 3000],  # One outlier
        'tire_age': [1, 2, 3]
    })
    
    result = SchemaValidator.validate_dataframe(
        df, 
        expected_columns=['lap_time', 'tire_age'],
        numeric_ranges={'lap_time': (50, 150)}
    )
    print(f"\n✓ DataFrame validation: score={result.data_quality_score}%")
    
    print("\n✓ Schema validator ready!")
