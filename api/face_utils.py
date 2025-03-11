import cv2
import mediapipe as mp
import numpy as np
import math

mp_face_mesh = mp.solutions.face_mesh

# Key landmark indices (MediaPipe's 468-point model)
LANDMARK_INDICES = {
    'LEFT_EYE': [33, 160, 158, 133, 153, 144],
    'RIGHT_EYE': [362, 385, 387, 263, 373, 380],
    'JAWLINE': [172, 136, 150, 149, 176, 148, 152, 377, 400, 378, 379, 365, 397, 288],
    'NOSE_TIP': 4,
    'FOREHEAD': 10,
    'CHIN': 152,
    'LEFT_CHEEK': 454,
    'RIGHT_CHEEK': 234,
    'PHILTRUM_TOP': 0,
    'PHILTRUM_BOTTOM': 2,
    'UPPER_LIP': 13,
    'LOWER_LIP': 14
}

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def calculate_buccal_fat(landmarks):
    """Buccal fat calculation with minimal score reduction curve"""
    try:
        # Get landmarks
        left_cheek = landmarks[LANDMARK_INDICES['LEFT_CHEEK']]
        right_cheek = landmarks[LANDMARK_INDICES['RIGHT_CHEEK']]
        chin = landmarks[LANDMARK_INDICES['CHIN']]
        forehead = landmarks[LANDMARK_INDICES['FOREHEAD']]
        
        # Calculate proportions
        face_height = abs(forehead.y - chin.y)
        face_width = abs(landmarks[234].x - landmarks[454].x)
        
        # Calculate cheek prominence using 3D proportional analysis
        vertical_protrusion = ((chin.y - left_cheek.y) + (chin.y - right_cheek.y)) / 2
        horizontal_ratio = face_width / face_height
        
        # Combined metric with non-linear scaling
        combined_metric = (vertical_protrusion * horizontal_ratio) ** 0.7
        
        # Ultra-gentle scoring curve
        score = np.interp(combined_metric,
                         [0.02, 0.05, 0.10, 0.15],  # Wider input range
                         [10.0, 9.5,  7.0,  4.0])    # Gradual descent
        
        # Apply soft clipping with bonus points
        final_score = score * 0.9 + 3.0  # Base score boost
        return round(np.clip(final_score, 5.0, 10.0), 1)  # Hard floor at 5.0
    except Exception as e:
        print(f"Buccal Fat error: {str(e)}")
        return 7.5  # High default to prevent low scores


def calculate_under_eye(image, landmarks):
    """More forgiving under-eye analysis"""
    try:
        def get_under_eye_mask(eye_points):
    # Correct tuple formation
            points = [(int(p.x * image.shape[1]), 
                int(p.y * image.shape[0])) 
             for p in [landmarks[i] for i in eye_points]]
            hull = cv2.convexHull(np.array(points))
            mask = np.zeros(image.shape[:2], dtype=np.uint8)
            cv2.fillConvexPoly(mask, hull, 255)
            return cv2.GaussianBlur(mask, (51, 51), 0)

        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel = lab[:,:,0]
        
        def analyze_eye(mask):
            region = l_channel[np.where(mask > 127)]
            if region.size < 100:
                return (0.15, 0.45)  # More favorable defaults
            
            face_light = np.percentile(l_channel, 70)  # Lower percentile
            eye_light = np.percentile(region, 30)      # Higher percentile
            darkness = (face_light - eye_light) / face_light
            
            b_channel = lab[:,:,2]
            yellow = np.mean(b_channel[np.where(mask > 127)]) / 255
            return (darkness, yellow)

        left_mask = get_under_eye_mask(LANDMARK_INDICES['LEFT_EYE'])
        right_mask = get_under_eye_mask(LANDMARK_INDICES['RIGHT_EYE'])
        
        l_dark, l_yellow = analyze_eye(left_mask)
        r_dark, r_yellow = analyze_eye(right_mask)
        
        avg_dark = (l_dark + r_dark) / 2
        avg_yellow = (l_yellow + r_yellow) / 2
        
        # Less aggressive scoring curves
        # Modified scoring with boosted base values
        darkness_score = 10 * (1 - sigmoid(avg_dark*4 - 1))  # Flatter curve
        yellow_score = 10 * (1 - sigmoid(avg_yellow*3 - 1.5))  # Reduced impact
        final_score = (darkness_score * 0.5) + (yellow_score * 0.3) + 4.5  # Base boost
        
        return round(np.clip(final_score, 5.5, 10.0), 1)  # Higher floor
    except Exception as e:
        print(f"Under-Eye error: {str(e)}")
        return 7.0  # Boosted default


def calculate_skin_clarity(image):
    """Skin analysis with dynamic range adjustment"""
    try:
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        texture = cv2.Laplacian(gray, cv2.CV_64F).var()
        color_uniformity = np.std(lab[:,:,1]) + np.std(lab[:,:,2])
        
        denoised = cv2.fastNlMeansDenoising(gray)
        _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        blemish_score = len([c for c in contours if 10 < cv2.contourArea(c) < 500])
        
        t_score = np.interp(texture, [150, 600], [10, 0])
        c_score = np.interp(color_uniformity, [25, 75], [10, 0])
        b_score = np.interp(blemish_score, [0, 15], [10, 0])
        
        final_score = (t_score*0.4 + c_score*0.3 + b_score*0.3)
        return round(np.clip(final_score, 4.0, 9.5), 1)
    except Exception as e:
        print(f"Skin Clarity error: {str(e)}")
        return 6.5

def calculate_symmetry(landmarks):
    """Calculate facial symmetry score"""
    try:
        pairs = [(162, 391), (21, 251), (54, 284), 
                (103, 333), (67, 297), (109, 338)]
        
        face_width = abs(landmarks[234].x - landmarks[454].x)
        differences = [abs(landmarks[left].x - (1 - landmarks[right].x))/face_width
                      for left, right in pairs]
        
        avg_diff = np.mean(differences)
        score = 10 - (avg_diff * 20)
        return round(np.clip(score, 4.5, 9.8), 1)
    except Exception as e:
        print(f"Symmetry error: {str(e)}")
        return 6.2

def calculate_golden_ratio(landmarks):
    """Facial proportions analysis"""
    try:
        face_width = abs(landmarks[LANDMARK_INDICES['RIGHT_CHEEK']].x - 
                       landmarks[LANDMARK_INDICES['LEFT_CHEEK']].x)
        face_height = abs(landmarks[LANDMARK_INDICES['CHIN']].y - 
                        landmarks[LANDMARK_INDICES['FOREHEAD']].y)
        
        ratio = face_height / face_width if face_width > 0.001 else 1.0
        golden_diff = abs(ratio - 1.618)
        return round(np.clip(10 - (golden_diff * 2.5), 5.0, 9.9), 1)
    except Exception as e:
        print(f"Golden Ratio error: {str(e)}")
        return 6.7

def calculate_canthal_tilt(landmarks):
    """Canthal tilt analysis with improved angle calculation"""
    try:
        left_outer, left_inner = landmarks[33], landmarks[133]
        right_outer, right_inner = landmarks[362], landmarks[263]

        def get_angle(a, b):
            dx, dy = b.x - a.x, b.y - a.y
            return math.degrees(math.atan2(dy, dx))

        angles = [get_angle(left_outer, left_inner), 
                 get_angle(right_inner, right_outer)]
        avg_angle = np.mean(angles)
        
        score = np.interp(avg_angle, [-5, 5, 15, 25], [4.0, 7.5, 9.5, 6.0])
        return round(score, 1)
    except Exception as e:
        print(f"Canthal Tilt error: {str(e)}")
        return 6.5

def calculate_jawline_score(landmarks):
    """Jawline analysis with improved angle calculation"""
    try:
        chin = landmarks[152]
        left_jaw = landmarks[172]
        right_jaw = landmarks[397]

        vec_left = (left_jaw.x - chin.x, left_jaw.y - chin.y)
        vec_right = (right_jaw.x - chin.x, right_jaw.y - chin.y)

        dot = sum(a*b for a, b in zip(vec_left, vec_right))
        mag_left = math.hypot(*vec_left)
        mag_right = math.hypot(*vec_right)
        
        angle = math.degrees(math.acos(dot/(mag_left*mag_right)))
        return round(np.clip((150 - angle) * 0.18, 5.5, 9.7), 1)
    except Exception as e:
        print(f"Jawline error: {str(e)}")
        return 6.8

def calculate_philtrum_ratio(landmarks):
    """Philtrum-to-chin ratio analysis"""
    try:
        philtrum_height = abs(landmarks[0].y - landmarks[2].y)
        chin_height = abs(landmarks[13].y - landmarks[152].y)
        
        if chin_height < 0.001:
            return 6.5
            
        ratio = philtrum_height / chin_height
        return round(10 - abs(ratio - 0.25) * 18, 1)
    except Exception as e:
        print(f"Philtrum error: {str(e)}")
        return 6.3

def analyze_face(image_path):
    """Main analysis function with improved error handling"""
    try:
        img = cv2.imread(image_path)
        if img is None or img.size == 0:
            print("Invalid image file")
            return None

        with mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.6) as face_mesh:
            
            results = face_mesh.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            if not results.multi_face_landmarks:
                print("No face detected")
                return None

            landmarks = results.multi_face_landmarks[0].landmark
            
            return {
                'Symmetry': calculate_symmetry(landmarks),
                'Canthal Tilt': calculate_canthal_tilt(landmarks),
                'Golden Ratio': calculate_golden_ratio(landmarks),
                'Jawline': calculate_jawline_score(landmarks),
                'Buccal Fat': calculate_buccal_fat(landmarks),
                'Skin Clarity': calculate_skin_clarity(img),
                'Under-Eye': calculate_under_eye(img, landmarks),
                'Philtrum Ratio': calculate_philtrum_ratio(landmarks)
            }
    except Exception as e:
        print(f"Analysis error: {str(e)}")
        return {
            'Symmetry': 6.5,
            'Canthal Tilt': 6.5,
            'Golden Ratio': 6.5,
            'Jawline': 6.5,
            'Buccal Fat': 6.5,
            'Skin Clarity': 6.5,
            'Under-Eye': 6.5,
            'Philtrum Ratio': 6.5
        }