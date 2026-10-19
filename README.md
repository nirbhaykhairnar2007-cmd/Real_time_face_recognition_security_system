# Real_time_face_recognition_security_system
An AI and IoT-based security system that uses real-time face recognition to verify users and automatically control door access, preventing unauthorized entry. 
# FaceLock: AI-Based Door Security System Using Face Recognition and IoT

## 📌 Project Overview
FaceLock is a smart security system that uses Artificial Intelligence (AI) and the Internet of Things (IoT) to control door access through real-time face recognition. It allows authorized users to enter while preventing unauthorized access.

## 🎯 Objectives
- Provide secure and automated door access.
- Recognize registered users using a camera.
- Control door locks based on authentication results.
- Store user details and access logs using Firebase.
- Enable real-time monitoring of the security system.

## ✨ Features
- Real-time face detection and recognition.
- Automatic access approval or denial.
- IoT-based door lock control using ESP32.
- Cloud data storage and access logging with Firebase.
- Simple graphical user interface using Tkinter.
- Support for multiple registered users.

## 🛠️ Technologies Used
- **Programming Language:** Python
- **Face Recognition:** OpenCV, face_recognition
- **AI/ML:** Deep Learning-based facial feature extraction
- **Database/Cloud:** Firebase
- **IoT Hardware:** ESP32
- **GUI:** Tkinter
- **Camera:** Webcam

## ⚙️ Methodology / Approach
1. **Face Capture:** The camera captures live video of the person standing in front of the system.
2. **Face Detection:** OpenCV detects the face from the captured video.
3. **Face Recognition:** The system extracts facial features and compares them with registered users.
4. **Authentication:** If the face matches an authorized user, access is granted; otherwise, access is denied.
5. **Door Control:** The ESP32 controls the electronic door lock according to the authentication result.
6. **Cloud Integration:** Firebase stores user information and access logs for monitoring.
7. **User Interface:** Tkinter provides an interface to interact with the system.

## 🔒 Applications
- Smart home security
- Office access control
- College laboratories
- Restricted areas
- Automated attendance systems

## 🔮 Future Enhancements
- Mobile application for remote access.
- Notifications for unauthorized access attempts.
- Improved recognition in low-light conditions.
- Multi-factor authentication using OTP or fingerprints.
- Enhanced data encryption and security.

## ⚠️ Limitations
- Recognition accuracy may be affected by poor lighting.
- Camera quality can affect system performance.
- Cloud features may require an internet connection.
- Only registered users can be authenticated.

## 👨‍💻 Conclusion
FaceLock combines AI, face recognition, cloud computing, and IoT to provide a smart and automated security solution. It reduces dependence on traditional keys and passwords while offering convenient access control and monitoring.

---
**Project Name:** FaceLock – Real time face recognition security system and IoT
