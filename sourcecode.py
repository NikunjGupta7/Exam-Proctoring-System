from tkinter import *
from PIL import Image, ImageTk
from tkinter import ttk
import cv2
import dlib
import face_recognition
import numpy as np
import threading
import time
import win32gui
import win32con
import csv

# Function to convert seconds to hours, minutes, and seconds
def convert_seconds(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return hours, minutes, seconds

# Function to display timer on webcam feed
def display_timer(frame, timer_seconds):
    if frame is not None:
        hours, minutes, seconds = convert_seconds(timer_seconds)
        timer_text = f'Time Remaining: {hours}h {minutes}m {seconds}s'
        font = cv2.FONT_HERSHEY_SIMPLEX
        org = (10, frame.shape[0] - 50)
        fontScale = 1
        color = (0, 255, 0)  # Green color for timer
        thickness = 2
        cv2.putText(frame, timer_text, org, font, fontScale, color, thickness, cv2.LINE_AA)
    else:
        print("Error : No Frame Detected")

def timer_function():
    global running, timer_seconds
    timer_seconds = 10800  # Set the timer for 3 hours
    while timer_seconds > 0 and running:
        time.sleep(1)
        timer_seconds -= 1
    running = False
    print("Timer finished.")

running = True
submit_requested = False
timer_seconds = 0

def save(frame, button):
    cv2.imwrite('Candidate.jpg', frame)
    button.config(text='Saved')


def generate_feedback_form(candidate_name):
    feedback_window = Tk()
    feedback_window.title("Feedback Form")
    feedback_window.geometry("800x600")

    feedback_label = Label(feedback_window, text="Feedback Form", font=("Arial", 18, "bold"))
    feedback_label.pack(pady=20)

    name_label = Label(feedback_window, text=f"Name: {candidate_name}", font=("Arial", 12))
    name_label.pack(anchor=W, padx=20)

    # Add explanation for the rating scale
    scale_explanation = Label(feedback_window, text="Please note: 1 represents Strongly Disagree/Poor/Dissatisfied and 5 represents Strongly Agree/Best/Very Satisfied", font=("Arial", 10))
    scale_explanation.pack(pady=10)

    questions = [
        "How satisfied are you with the clarity of the exam instructions?",
        "Did you receive adequate support from the instructors or support team before and during the exam?",
        "The quality of the online exam platform",
        "The online exam experience felt fair and stress-free",
        "Rate your overall experience with the exam."
    ]

    feedback_data = {}

    for idx, question in enumerate(questions):
        q_frame = Frame(feedback_window)
        q_frame.pack(anchor=W, padx=20, pady=10)

        q_label = Label(q_frame, text=f"{idx + 1}. {question}", width=60, anchor=W)
        q_label.pack(side=LEFT)

        q_var = IntVar()
        feedback_data[question] = q_var

        for i in range(1, 6):
            q_radio = Radiobutton(q_frame, text=str(i), variable=q_var, value=i)
            q_radio.pack(side=LEFT, padx=5)

    # Add entry for additional comments
    comments_label = Label(feedback_window, text="Additional Comments/Suggestions:", font=("Arial", 12))
    comments_label.pack(anchor=W, padx=20, pady=10)

    comments_text = Text(feedback_window, height=4, width=80)
    comments_text.pack(padx=20, pady=10)

    def submit_feedback():
        with open("feedback.txt", "a") as f:
            f.write(f"Name: {candidate_name}\n")
            f.write("Feedback:\n")
            for question, q_var in feedback_data.items():
                f.write(f"{question}: {q_var.get()}\n")
            f.write("Additional Comments/Suggestions:\n")
            f.write(comments_text.get("1.0", END))
            f.write("\n")
        feedback_window.destroy()

    submit_button = Button(feedback_window, text="Submit Feedback", command=submit_feedback)
    submit_button.pack(pady=20)

    feedback_window.mainloop()

# Create an instance of TKinter Window or frame
win = Tk()
detector = dlib.get_frontal_face_detector()

# Set the size of the window
win.geometry('640x630')
win.title('Setup')
# Keep the window on top
win.attributes('-topmost', True)

# Create a Label to capture the Video frames
image_label = Label(win)
image_label.grid(row=0, column=0, padx=10, pady=10)

text_label = Label(win, text='Face the camera!')
text_label.grid(row=1, column=0)

save_button = Button(win, text='Capture', state=DISABLED)
save_button.grid(row=2, column=0, padx=10, pady=10)

e = Entry(win, width=40)
e.grid(row=3, column=0)
e.insert(0, 'Enter your name here')

# Function to delete default text when entry widget is clicked
def delete_default_text(event):
    if e.get() == 'Enter your name here':
        e.delete(0, END)

# Bind the click event to the delete_default_text function
e.bind("<Button-1>", delete_default_text)

firstWindowRunning = True
def exit():
    global candidate_name 
    if e.get() == 'Enter your name here' or e.get() == 'Please enter a valid name':
        e.delete(0, END)
        e.insert(0, 'Please enter a valid name')
        return

    candidate_name = e.get()
    global firstWindowRunning
    firstWindowRunning = False
    win.destroy()

exit_button = Button(win, text='Start the exam', command=exit)
exit_button.grid(row=4, column=0, padx=10, pady=10)

cap = cv2.VideoCapture(0)

# Define function to show frame
def show_frames():
    # Get the latest frame and convert into Image 
    ret, frame = cap.read()

    if not ret:
        print("Error: Unable to capture frame from video source.")
        return

    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    saved_frame = frame.copy()
    faces = detector(gray_frame, 1)
    for face in faces:
        x1 = face.left()
        y1 = face.top()
        x2 = face.right()
        y2 = face.bottom()
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
    
    if len(faces) == 0:
        text_label.config(text='Face the camera!')
        save_button.config(state=DISABLED)
    elif len(faces) == 1:
        text_label.config(text='Great! Now hit "Capture" to save your photo.')
        save_button.config(state=NORMAL, command=lambda: save(saved_frame, save_button))
    else:
        text_label.config(text='Only one person allowed!')
        save_button.config(state=DISABLED)
    
    cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(cv2image)
    imgtk = ImageTk.PhotoImage(image=img)
    image_label.imgtk = imgtk
    image_label.configure(image=imgtk)
    time.sleep(0.02)

while firstWindowRunning:
    show_frames()
    win.update()

cap.release()

sample_image = face_recognition.load_image_file('Candidate.jpg')
candidate_face_encoding = face_recognition.face_encodings(sample_image)[0]

known_face_encodings = [candidate_face_encoding]
known_face_names = [candidate_name]

video_capture = cv2.VideoCapture(0)
face_locations = []
face_encodings = []
face_names = []
process_this_frame = True

# Create a named window and set it to always stay on top
cv2.namedWindow('Webcam Feed', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Webcam Feed', 640, 480)
cv2.setWindowProperty('Webcam Feed', cv2.WND_PROP_TOPMOST, 1)

def submit_exam(event, x, y, flags, param):
    global running, submit_requested
    if event == cv2.EVENT_LBUTTONDOWN:
        # Define button rectangle coordinates
        if 500 <= x <= 630 and 390 <= y <= 430:
            submit_requested = True
            running = False
            print("Exam submitted by user.")

# Set the mouse callback function
cv2.setMouseCallback('Webcam Feed', submit_exam)

def check_window_state():
    while running:
        hwnd = win32gui.FindWindow(None, 'Webcam Feed')
        if hwnd:
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
                print("WARNING: You cannot leave the screen!")
        time.sleep(1)

# Start the timer thread after the webcam feed is opened
timer_thread = threading.Thread(target=timer_function)
timer_thread.start()

# Start the window state check thread
window_state_thread = threading.Thread(target=check_window_state)
window_state_thread.start()

recognized_candidate_name = None  

# Main loop for capturing frames, displaying timer, and performing face recognition
while running:
    ret, frame = video_capture.read()
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    org = (10, 30)
    text = 'Click Submit if you have finished the exam'
    fontScale = 0.7  # Reduced font size to prevent overflow
    color = (0, 0, 255)
    thickness = 2
    cv2.putText(frame, text, org, font, fontScale, color, thickness, cv2.LINE_AA)

    # Draw the submit button above the warning message area
    button_color = (192, 192, 192)  # Silver color
    button_text_color = (0, 0, 0)  # Black text color
    button_top_left = (500, 390)
    button_bottom_right = (630, 430)
    cv2.rectangle(frame, button_top_left, button_bottom_right, button_color, -1)
    cv2.putText(frame, 'Submit', (510, 420), font, 0.8, button_text_color, 2, cv2.LINE_AA)

   

    # Display the timer on the webcam feed
    display_timer(frame, timer_seconds)

    if process_this_frame:
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        face_names = []
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"
            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]
            face_names.append(name)

    process_this_frame = not process_this_frame

    for (top, right, bottom, left), name in zip(face_locations, face_names):
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4
        error_color = (0, 0, 255)
        color = (0, 255, 0)

        if len(face_locations) == 1 and name == candidate_name:
            recognized_candidate_name = name
        else:
            recognized_candidate_name = None

        if recognized_candidate_name:
            name_to_display = recognized_candidate_name
            color = (0, 255, 0)  # Green color for recognized candidate name
        else:
            name_to_display = "Unknown"
            color = (0, 0, 255)  # Red color for "Unknown"

        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, -1)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

    # Detect if no face is detected or multiple faces are detected
    if len(face_locations) == 0:
        warning_text = 'WARNING! No face detected.'
    elif len(face_locations) > 1:
        warning_text = 'WARNING! Multiple faces detected.'
    else:
        warning_text = None

    if warning_text:
        font = cv2.FONT_HERSHEY_SIMPLEX
        bottom_left_corner = (10, frame.shape[0] - 10)
        cv2.putText(frame, warning_text, bottom_left_corner, font, 0.8, (0, 0, 255), 2)

    cv2.imshow('Webcam Feed', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# End the exam if the timer reaches 0 or if the submit button is clicked
if submit_requested:
    print("Exam was submitted early by the user.")
else:
    print("Exam ended due to timer.")

timer_thread.join()
video_capture.release()
cv2.destroyAllWindows()

# Generate feedback form after the exam is over
generate_feedback_form(candidate_name)