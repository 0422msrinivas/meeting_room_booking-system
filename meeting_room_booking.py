import datetime
import json
import os
import smtplib
import getpass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import random
import string
import bcrypt
import re


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        return super().default(obj)


class User:
    def __init__(self, username, password, salt, email):
        self.username = username
        self.password = password
        self.salt = salt
        self.email = email
        self.booking_file_path = f"{self.username}_bookings.json"

    def update_password(self, new_password, new_salt):
        self.password = new_password
        self.salt = new_salt


class ConsoleColors:
    # ANSI escape codes for text colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'  # Reset to default color


def print_colored_text(text, color):
    print(color + text + ConsoleColors.RESET)


class MeetingRoomBookingSystem:
    def __init__(self):
        self.room_names = [f"Room{i}" for i in range(1, 11)]
        self.bookings = []
        self.users = []
        self.current_user = None
        self.load_users_from_file()

    def save_users_to_file(self):
        with open("users.json", "w") as file:
            users_data = [
                {"username": user.username, "password": user.password, "salt": user.salt, "email": user.email}
                for user in self.users
            ]
            json.dump(users_data, file)

    def load_users_from_file(self):
        try:
            with open("users.json", "r") as file:
                users_data = json.load(file)
                self.users = [
                    User(
                        user_data.get("username", ""),
                        user_data.get("password", ""),
                        user_data.get("salt", ""),
                        user_data.get("email", "")
                    ) for user_data in users_data
                ]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print_colored_text(f"Error loading users from file: {e}", ConsoleColors.RED)

    def save_user(self, username, hashed_password, salt, email):
        self.users.append(User(username, hashed_password, salt, email))
        self.save_users_to_file()

    def load_user(self, username):
        return next((user for user in self.users if user.username == username), None)

    def signup(self):
        username = input("Enter your username: ")
        password = getpass.getpass("Enter your password: ")
        email = input("Enter your email: ")
        if not self.is_valid_email(email):
            print_colored_text("Invalid email format. Please enter a valid email.", ConsoleColors.RED)
            return

        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        self.save_user(username, hashed_password.decode('utf-8'), salt.decode('utf-8'), email)

        print_colored_text("Sign up successful!", ConsoleColors.GREEN)

    def login(self):
        username = input("Enter your username: ")
        password = getpass.getpass("Enter your password: ")

        user = self.load_user(username)

        if user:
            salt = user.salt.encode('utf-8')
            hashed_password = user.password.encode('utf-8')

            input_hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

            if hashed_password == input_hashed_password:
                print_colored_text("Login successful!", ConsoleColors.GREEN)
                self.current_user = user
                self.load_user_bookings()
                return True
            else:
                print_colored_text("Incorrect password.", ConsoleColors.RED)
        else:
            print_colored_text("User not found.", ConsoleColors.RED)
        return False

    def is_valid_email(self, email):
        email_regex = r'^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_regex, email) is not None

    def forgot_password(self, username):
        user = self.load_user(username)
        if user:
            entered_email = input("Enter your email: ")

            if entered_email == user.email and self.is_valid_email(entered_email):
                otp = self.generate_otp()
                self.send_otp_email(username, entered_email, otp)
                user_input_otp = input("Enter the OTP sent to your email: ")

                if user_input_otp == otp:
                    new_password = getpass.getpass("Enter your new password: ")

                    new_salt = bcrypt.gensalt()

                    new_hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), new_salt)

                    user.update_password(new_hashed_password.decode('utf-8'), new_salt.decode('utf-8'))
                    self.save_users_to_file()
                    print_colored_text("Password reset successful. You can now log in with your new password.",
                                       ConsoleColors.GREEN)
                else:
                    print_colored_text("Invalid OTP. Password reset failed.", ConsoleColors.RED)
            else:
                print_colored_text("Invalid email or email format.", ConsoleColors.RED)
        else:
            print_colored_text("User not found.", ConsoleColors.RED)

    def generate_otp(self):
        return ''.join(random.choices(string.digits, k=6))

    def send_otp_email(self, username, to_email, otp):
        subject = "Password Reset OTP"
        body = f"Dear {username},\n\nYour OTP for password reset is: {otp}\n\nThis OTP is valid for a single use only."

        try:
            self.send_email(subject, body, to_email)
            print_colored_text("OTP sent successfully. Check your email.", ConsoleColors.GREEN)
        except Exception as e:
            print_colored_text(f"Error sending OTP email: {e}", ConsoleColors.RED)

    # ... (continue with the rest of the code)
    def display_room_dropdown(self):
        print("Room Options:")
        for index, room_name in enumerate(self.room_names, start=1):
            print_colored_text(f"{index}. {room_name}",ConsoleColors.YELLOW)
        room_index = int(self.get_valid_input("Enter the room number: ", [str(i) for i in range(1, len(self.room_names) + 1)])) - 1
        return room_index

  
    def save_user_bookings(self):
        with open(self.current_user.booking_file_path, "w") as file:
            json.dump(self.bookings, file, cls=DateTimeEncoder)
    def load_user_bookings(self):
        try:
            with open(self.current_user.booking_file_path, "r") as file:
                file_content = file.read().strip()
                if file_content:
                    self.bookings = json.loads(file_content)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    def get_valid_input(self, prompt, valid_options):
        while True:
            user_input = input(prompt).strip().lower()
            if user_input in valid_options:
                return user_input
            else:
                print("Invalid input. Please try again.")
    def create_booking(self, room_index, start_time, end_time):
        try:
            room_name = self.room_names[room_index]

            start_time = self.validate_datetime(start_time)
            end_time = self.validate_datetime(end_time)

           
            if start_time < datetime.datetime.now():
                print("Error: Booking time must be in the future.")
                return

            if start_time >= end_time:
                print("Error: End time must be after start time.")
                return

            new_booking = {
                'room_name': room_name,
                'start_time': start_time,
                'end_time': end_time
            }

            if not self.has_conflict(new_booking):
                self.bookings.append(new_booking)
                print("Booking created successfully.")
                self.save_user_bookings()

               
                self.send_booking_confirmation_email(new_booking)
            else:
                print("Error: Room already booked for the given time slot. Removing the room from available rooms.")
                self.room_names.pop(room_index)
                print(f"Available rooms: {', '.join(self.room_names)}")

        except ValueError:
            print("Error: Invalid date-time format. Please use 'YYYY-MM-DD HH:MM:SS'.")

    def update_booking(self, index, room_index, start_time, end_time):
        try:
            room_name = self.room_names[room_index]

            start_time = self.validate_datetime(start_time)
            end_time = self.validate_datetime(end_time)

            if start_time >= end_time:
                print("Error: End time must be after start time.")
                return

            updated_booking = {
                'room_name': room_name,
                'start_time': start_time,
                'end_time': end_time
            }

            if not self.has_conflict(updated_booking, index):
                self.bookings[index - 1] = updated_booking
                print("Booking updated successfully.")
                self.save_user_bookings()

               
                self.send_booking_update_email(updated_booking)
            else:
                print("Error: Room already booked for the given time slot. Removing the room from available rooms.")
                self.room_names.pop(room_index)
                print(f"Available rooms: {', '.join(self.room_names)}")

        except ValueError:
            print("Error: Invalid date-time format. Please use 'YYYY-MM-DD HH:MM:SS'.")

    def delete_booking(self, index):
        if 1 <= index <= len(self.bookings):
            deleted_room_name = self.bookings[index - 1]['room_name']
            del self.bookings[index - 1]
            self.room_names.append(deleted_room_name)
            print(f"Booking deleted successfully. Room {deleted_room_name} added back to available rooms.")
            print(f"Available rooms: {', '.join(self.room_names)}")
            self.save_user_bookings()
        else:
            print("Error: Invalid booking index.")

    def has_conflict(self, new_booking, exclude_index=None):
        for i, booking in enumerate(self.bookings):
            if i == exclude_index:
                continue

            if (new_booking['room_name'] == booking['room_name'] and
                    ((new_booking['start_time'] >= booking['start_time'] and new_booking['start_time'] < booking['end_time']) or
                     (new_booking['end_time'] > new_booking['start_time'] and new_booking['end_time'] <= booking['end_time']))):
                return True

        return False

    def read_bookings(self):
        if not self.bookings:
            print("No bookings found.")
        else:
            for index, booking in enumerate(self.bookings, start=1):
                print(f"{index}. Room: {booking['room_name']}, Start Time: {booking['start_time']}, End Time: {booking['end_time']}")

    def validate_datetime(self, datetime_str):
        try:
            return datetime.datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            print("Error: Invalid date-time format. Please use 'YYYY-MM-DD HH:MM:SS'.")
            return None



    def send_email(self, subject, body, to_email, attachment_path=None):
        sender_email = "0422msrinivasa@gmail.com"
        sender_password = 'knnv pqei oxgz uanv'
        smtp_server = 'smtp.gmail.com'
        smtp_port = 587

        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = to_email
        message['Subject'] = subject

        message.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, message.as_string())

    def send_booking_confirmation_email(self, booking):
        subject = "Meeting Room Booking Confirmation"
        body = f"Dear {self.current_user.username},\n\nYour booking details:\nRoom: {booking['room_name']}\nStart Time: {booking['start_time']}\nEnd Time: {booking['end_time']}\n\nThank you for using our meeting room booking system!"

        to_email = self.current_user.email
        if to_email:
            try:
                self.send_email(subject, body, to_email)
                print_colored_text("Booking confirmation email sent successfully.", ConsoleColors.GREEN)
            except Exception as e:
                print_colored_text(f"Error sending booking confirmation email: {e}", ConsoleColors.RED)
        else:
            print_colored_text("Error: User email address is empty. Unable to send confirmation email.", ConsoleColors.RED)

    # ... (continue with the rest of the code)
    def send_booking_update_email(self, booking):
        subject = "Meeting Room Booking Update"
        body = f"Dear {self.current_user.username},\n\nYour booking has been updated:\nRoom: {booking['room_name']}\nStart Time: {booking['start_time']}\nEnd Time: {booking['end_time']}\n\nThank you for using our meeting room booking system!"

        to_email = self.current_user.email
        if to_email:
            try:
                self.send_email(subject, body, to_email)
                print("Booking update email sent successfully.")
            except Exception as e:
                print(f"Error sending booking update email: {e}")
        else:
            print("Error: User email address is empty. Unable to send update email.")



if __name__ == "__main__":
    booking_system = MeetingRoomBookingSystem()

    while True:
      
        print_colored_text("\n\t\t\t==========Menu:==========\t\t\t",ConsoleColors.RED)
        
        print_colored_text("\t\t\t1. Sign Up\t\t\t",ConsoleColors.CYAN)
        print_colored_text("\t\t\t2. Log In\t\t\t",ConsoleColors.CYAN)
        print_colored_text("\t\t\t3. Forgot Password\t\t\t",ConsoleColors.CYAN)
        print_colored_text("\t\t\t4. Exit\t\t\t",ConsoleColors.CYAN)

        authentication_choice = input("Enter your choice: ")

        if authentication_choice == '1':
            booking_system.signup()
        elif authentication_choice == '2':
            if booking_system.current_user:
                print_colored_text("You are already logged in.", ConsoleColors.YELLOW)
            else:
                booking_system.login()
        elif authentication_choice == '3':
            username = input("Enter your username: ")
            booking_system.forgot_password(username)
        elif authentication_choice == '4':
            booking_system.save_users_to_file()
            break
        else:
            print_colored_text("Invalid choice. Please enter a number from 1 to 4.", ConsoleColors.RED)

        while booking_system.current_user:
            print_colored_text("\n\t\t\t==========Booking Menu:=========\t\t\t",ConsoleColors.BLUE)
            print_colored_text("\t\t\t1. Create Booking\t",ConsoleColors.BLUE)
            print_colored_text("\t\t\t2. Read Bookings\t\t\t",ConsoleColors.BLUE)
            print_colored_text("\t\t\t3. Update Booking\t\t\t",ConsoleColors.BLUE)
            print_colored_text("\t\t\t4. Delete Booking\t\t\t",ConsoleColors.BLUE)
            print_colored_text("\t\t\t5. Log Out\t\t\t",ConsoleColors.BLUE)
            print_colored_text("\t\t\t6. Exit\t\t\t",ConsoleColors.BLUE)

            choice = input("Enter your choice: ")

            if choice == '1':
                room_index = booking_system.display_room_dropdown()
                start_time = input("Enter start time (YYYY-MM-DD HH:MM:SS): ")
                end_time = input("Enter end time (YYYY-MM-DD HH:MM:SS): ")
                booking_system.create_booking(room_index, start_time, end_time)
            elif choice == '2':
                booking_system.read_bookings()
            elif choice == '3':
                index = int(input("Enter the index of the booking to update: "))
                room_index = booking_system.display_room_dropdown()
                start_time = input("Enter new start time (YYYY-MM-DD HH:MM:SS): ")
                end_time = input("Enter new end time (YYYY-MM-DD HH:MM:SS): ")
                booking_system.update_booking(index, room_index, start_time, end_time)
            elif choice == '4':
                index = int(input("Enter the index of the booking to delete: "))
                booking_system.delete_booking(index)
            elif choice == '5':
                booking_system.current_user = None
                print_colored_text("You have been logged out.", ConsoleColors.YELLOW)
            elif choice == '6':
                booking_system.current_user = None
                break
            else:
                print_colored_text("Invalid choice. Please enter a number from 1 to 6.", ConsoleColors.RED)

    print_colored_text("Exiting the meeting room booking system", ConsoleColors.GREEN)
