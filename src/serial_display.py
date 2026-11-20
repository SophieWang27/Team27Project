"""Send a small newline-delimited status message to the Arduino over USB serial."""

import time


class SerialDisplay:
    """Optional serial link; the camera app still runs when no Arduino is set."""

    def __init__(self, port: str | None, baud_rate: int) -> None:
        self._connection = None
        self._last_message: str | None = None
        self._incoming = bytearray()
        if not port:
            print("Arduino serial output disabled (SERIAL_PORT is empty).")
            return

        try:
            import serial

            self._connection = serial.Serial(port, baud_rate, timeout=1)
            # Opening an Uno serial port may reset the board; give its sketch time to restart.
            time.sleep(2)
            print(f"Arduino display connected on {port} at {baud_rate} baud.")
        except Exception as exc:  # Keep camera-only operation available during setup.
            print(f"Could not open Arduino serial port {port}: {exc}")

    def send(self, mode: str, completed: int, status: str, feedback: str) -> None:
        """Send only changed display states to reduce serial traffic."""
        if self._connection is None:
            return
        safe_status = status.replace("|", " ").replace("\n", " ")[:16]
        safe_feedback = feedback.replace("|", " ").replace("\n", " ")[:48]
        message = f"{mode}|{completed}|{safe_status}|{safe_feedback}\n"
        if message == self._last_message:
            return
        try:
            self._connection.write(message.encode("ascii", errors="replace"))
            self._last_message = message
        except Exception as exc:
            print(f"Arduino serial write failed: {exc}")
            self.close()

    def poll_mode_change(self) -> bool:
        """Read a non-blocking MODE_NEXT event from the optional Arduino button."""
        if self._connection is None:
            return False
        try:
            waiting = self._connection.in_waiting
            if waiting:
                self._incoming.extend(self._connection.read(waiting))
            mode_next = False
            while b"\n" in self._incoming:
                line, _, rest = self._incoming.partition(b"\n")
                self._incoming = bytearray(rest)
                if line.strip() == b"MODE_NEXT":
                    mode_next = True
            return mode_next
        except Exception as exc:
            print(f"Arduino serial read failed: {exc}")
            self.close()
            return False

    def close(self) -> None:
        """Close the serial port if it was opened."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None
