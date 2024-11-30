import curses
from database import PasswordManager
from authentication import generate_qr_code
import time

def display_timed_message(stdscr, message, duration=2):
    stdscr.addstr(message)
    stdscr.refresh()
    time.sleep(duration)

def display_temporary_message(stdscr, message):
    stdscr.clear()
    stdscr.addstr(0, 0, message)
    stdscr.addstr("\n\nPress 'q' to clear this message.")
    stdscr.refresh()
    while True:
        key = stdscr.getch()
        if key == ord('q'):
            break
    stdscr.clear()
    stdscr.refresh()

def get_user_input(stdscr, prompt):
    stdscr.addstr(prompt)
    stdscr.refresh()
    curses.echo()
    user_input = stdscr.getstr().decode()
    curses.noecho()
    return user_input

def main(stdscr):
    try:
        pm = PasswordManager()
    except RuntimeError as e:
        display_timed_message(stdscr, str(e))
        return
    authenticated_user = None

    while True:
        stdscr.clear()
        stdscr.addstr("Password Manager CLI\n")

        if authenticated_user:
            stdscr.addstr(f"Logged in as: {authenticated_user}\n")
            stdscr.addstr("1. Add Password\n")
            stdscr.addstr("2. Get All Passwords for a Service\n")
            stdscr.addstr("3. Get All Passwords\n")
            stdscr.addstr("4. Logout\n")
            stdscr.addstr("5. Exit\n")
        else:
            stdscr.addstr("1. Register User\n")
            stdscr.addstr("2. Login User\n")
            stdscr.addstr("3. Exit\n")
        
        stdscr.addstr("Choose an option: ")
        stdscr.refresh()
        curses.echo()
        choice = stdscr.getstr().decode()
        curses.noecho()

        if authenticated_user:
            if choice == '1':
                try:
                    service = get_user_input(stdscr, "Enter service name: ")
                    service_username = get_user_input(stdscr, "Enter service username: ")
                    service_password = get_user_input(stdscr, "Enter service password: ")
                    response = pm.add_service(authenticated_user, service, service_username, service_password)
                    if response == "Update":
                        display_timed_message(stdscr, f'Password for {service} for user {authenticated_user} was updated.\n')
                    elif response == "Insert":
                        display_timed_message(stdscr, f'Password for {service} for user {authenticated_user} was added.\n')
                except RuntimeError as e:
                    display_timed_message(stdscr, str(e))

            elif choice == '2':
                try:
                    service = get_user_input(stdscr, "Enter service name: ")
                    credentials = pm.get_all_pass_by_serv(authenticated_user, service)
                    response = '\n'.join([f'Username: {user}, Password: {pwd}' for user, pwd in credentials])
                    display_temporary_message(stdscr, f'All credentials for {service}:\n{response}')
                except RuntimeError as e:
                    display_timed_message(stdscr, str(e))
                except ValueError as e:
                    display_timed_message(stdscr, str(e))

            elif choice == '3':
                try:
                    credentials = pm.get_all_pass(authenticated_user)
                    response = '\n'.join([f'Service: {service}, Username: {user}, Password: {pwd}' for service, user, pwd in credentials])
                    display_temporary_message(stdscr, f'All credentials saved by {authenticated_user}:\n{response}')
                except RuntimeError as e:
                    display_timed_message(stdscr, str(e))
                except ValueError as e:
                    display_timed_message(stdscr, str(e))

            elif choice == '4':
                authenticated_user = None
                display_timed_message(stdscr, "Logged out successfully.\n")

            elif choice == '5':
                break

            else:
                display_timed_message(stdscr, "Invalid option. Please try again.\n")

        else:
            if choice == '1':
                try:
                    username = get_user_input(stdscr, "Enter username: ")
                    password = get_user_input(stdscr, "Enter password: ")
                    otp_secret = pm.register_user(username, password)
                    qr_file_path = generate_qr_code(username, otp_secret)
                    display_timed_message(stdscr, f'User {username} registered successfully! Scan this QR code with Google Authenticator: {qr_file_path}\n')
                except ValueError as e:
                    display_timed_message(stdscr, str(e))

            elif choice == '2':
                try:
                    username = get_user_input(stdscr, "Enter username: ")
                    password = get_user_input(stdscr, "Enter password: ")
                    otp_code = get_user_input(stdscr, "Enter OTP code: ")
                    pm.authenticate_user(username, password, otp_code)
                    authenticated_user = username
                    display_timed_message(stdscr, f'User {username} authenticated successfully!\n')
                except RuntimeError as e:
                    display_timed_message(stdscr, str(e))
                except ValueError as e:
                    display_timed_message(stdscr, str(e))

            elif choice == '3':
                break

            else:
                display_timed_message(stdscr, "Invalid option. Please try again.\n")

        stdscr.refresh()

    pm.close()


if __name__ == '__main__':
    curses.wrapper(main)