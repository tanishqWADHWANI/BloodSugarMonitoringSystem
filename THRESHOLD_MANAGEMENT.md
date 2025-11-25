# Threshold Management Feature

## Overview
Staff can now input, modify, and delete blood sugar thresholds for patients through the thresholds management interface.

## Accessing the Feature
1. Login as staff
2. Navigate to Staff Dashboard
3. Click "Open Thresholds" button
4. You will be redirected to the Threshold Management page

## How It Works

### Add Threshold
1. Select the **Status** type:
   - `Normal (max)` - Maximum value for normal readings
   - `Borderline (max)` - Maximum value for borderline readings
   - `AbnormalLow (min)` - Minimum threshold for abnormally low readings
   - `AbnormalHigh (max)` - Maximum threshold for abnormally high readings

2. Enter the **Value** in mg/dL (20-600 range)

3. Select **Scope**:
   - `SystemDefault` - Applies to user_id 0 (system-wide defaults)
   - `PatientOverride` - Specific to one patient (requires Patient ID)

4. If Patient Override is selected, enter the **Patient ID**

5. Click **Add Threshold**

### View Thresholds
The table shows all thresholds with:
- ID - Unique threshold identifier
- Status - The threshold type (normal/borderline/abnormal)
- Value - The range in mg/dL
- Scope - Whether it's system default or patient override
- Patient - Patient name (if override) or "-" (if system default)
- Actions - Delete button

### Delete Threshold
Click the **Delete** button next to any threshold to remove it.

### Reset to Defaults
Click **Reset to Defaults** to create system default thresholds:
- Normal: 70-130 mg/dL
- Borderline: up to 180 mg/dL
- Abnormal Low: 70 mg/dL

## API Endpoints

### GET /api/thresholds
Returns all thresholds in the system.

**Response:**
```json
{
  "count": 2,
  "thresholds": [
    {
      "threshold_id": 1,
      "user_id": 1,
      "status": "normal",
      "min_value": 70.0,
      "max_value": 130.0,
      "patient_name": "Demo User",
      "created_at": "Thu, 23 Oct 2025 00:24:42 GMT"
    }
  ]
}
```

### POST /api/thresholds/<user_id>
Create or update a threshold for a specific user.

**Request Body:**
```json
{
  "status": "normal",
  "minValue": 70,
  "maxValue": 130
}
```

**Response:**
```json
{
  "thresholdId": 2,
  "message": "Threshold set successfully"
}
```

### DELETE /api/thresholds/<threshold_id>
Delete a threshold by its ID.

**Response:**
```json
{
  "message": "Threshold deleted successfully"
}
```

## Database Schema
The thresholds are stored in the `thresholds` table:
- `threshold_id` - Primary key
- `user_id` - Foreign key to users (0 for system defaults)
- `status` - ENUM('normal', 'borderline', 'abnormal')
- `min_value` - Minimum threshold (decimal)
- `max_value` - Maximum threshold (decimal)
- `created_at` - Timestamp

## Notes
- Staff can set per-patient thresholds that override system defaults
- The frontend automatically converts the UI status types to backend enum values
- When a threshold exists for a user+status combination, POST will update it
- System defaults should use user_id = 0
- Patient overrides take precedence over system defaults when evaluating readings
