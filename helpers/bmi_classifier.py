def bmi_classifier(weight, height, age):
    """
    Determine BMI category.

    :param weight: Weight in kilograms
    :param height: Height in centimeters
    :param age: Age in years
    :return: BMI category
    """
    # Convert height from cm to m
    height_m = height / 100

    # Calculate BMI
    bmi = weight / (height_m ** 2)
    if age <= 20:
        # For age <= 20, use the CDC BMI-for-age percentiles
        if bmi < 5:
            return "underweight"
        elif 5 <= bmi < 85:
            return "normal"
        elif 85 <= bmi < 95:
            return "overweight"
        else:
            return "obese"

    # Determine BMI category
   if bmi < 18.5:
        return "underweight"
    elif 18.5 <= bmi < 25:
        return "normal"
    elif 25 <= bmi < 30:
        return "overweight"
    else:
        return "obese"