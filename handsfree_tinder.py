from __future__ import division
from google.cloud import speech
from selenium import webdriver
from bs4 import BeautifulSoup
import pyaudio
import queue
import re
import sys
import time
import pyautogui

class Tinder:
    def __init__(self, url: str, driver_path: str) -> None:
        self.url = url                                                                    # URL for selenium
        self.options = webdriver.ChromeOptions()                                          # Standard for using Chrome with selenium
        self.options.add_experimental_option('debuggerAddress', 'localhost:9222')         # Running Chrome on localhost
        self.driver = webdriver.Chrome(executable_path=driver_path, options=self.options) # Standard for using Chrome with selenium

    def __repr__(self) -> str:
        return 'This class is intended to be used in conjunction with the microphone so Tinder can be used in a handsfree manner.'

    def log_in(self) -> None:
        # Open the URL in Chrome
        self.driver.get(url=self.url)
        time.sleep(3)

    def get_div_id(self) -> str:
        # Get the current page's HTML
        html = self.driver.page_source

        # Create a soup object
        soup = BeautifulSoup(html, 'html.parser')

        # Find the div's id for the div that holds the profile cards. This is important because Tinder frequently changes this id, the class name, etc.
        global div_id

        div_id = soup.find('div', {'class': 'H(100%) Ov(h)'})['id']

        return div_id

class MicrophoneStream(object):
    """Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            # The API currently only supports 1-channel (mono) audio https://goo.gl/z757pE
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b''.join(data)

def listen_print_loop(responses):
    """Iterates through server responses and prints them.

    The responses passed is a generator that will block until a response
    is provided by the server.

    Each response may contain multiple results, and each result may contain
    multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
    print only the transcription for the top alternative of the top result.

    In this case, responses are provided for interim results as well. If the
    response is an interim one, print a line feed at the end of it, to allow
    the next result to overwrite it, until the response is a final one. For the
    final one, print a newline to preserve the finalized transcription.
    """
    num_chars_printed = 0

    for response in responses:
        if not response.results:
            continue

        # The `results` list is consecutive. For streaming, we only care about
        # the first result being considered, since once it's `is_final`, it
        # moves on to considering the next utterance.
        result = response.results[0]
        if not result.alternatives:
            continue

        # Display the transcription of the top alternative.
        transcript = result.alternatives[0].transcript

        """<CODE FOR TINDER>"""
        # Display the next picture
        if transcript.strip().lower() == 'next' and result.is_final:
            pyautogui.moveTo(x=1230, y=462, duration=0.1)
            time.sleep(0.1)
            pyautogui.click()

        # Display the previous picture
        if transcript.strip().lower() == 'previous' and result.is_final:
            pyautogui.moveTo(x=1053, y=462, duration=0.1)
            time.sleep(0.1)
            pyautogui.click()

        # Rewind to see the previous profile
        if transcript.strip().lower() == 'rewind' and result.is_final:
            try:
                tinder.driver.find_element_by_xpath(xpath=f'//*[@id="{div_id}"]/div/div[1]/div/main/div[1]/div/div/div[1]/div[1]/div/div[5]/div/div[1]/button').click()
            except Exception as e:
                print(str(e))

        # Swipe right or swipe left                   
        if transcript.strip().lower() == 'right' and result.is_final:
            try:
                tinder.driver.find_element_by_xpath(xpath=f'//*[@id="{div_id}"]/div/div[1]/div/main/div[1]/div/div/div[1]/div[1]/div/div[5]/div/div[4]/button').click()
            except Exception:
                tinder.driver.find_element_by_xpath(xpath=f'//*[@id="{div_id}"]/div/div[1]/div/main/div[1]/div/div/div[1]/div[1]/div/div[4]/div/div[4]/button').click()
            finally:
                time.sleep(1)
        elif transcript.strip().lower() == 'left' and result.is_final:
            try:                                          
                tinder.driver.find_element_by_xpath(xpath=f'//*[@id="{div_id}"]/div/div[1]/div/main/div[1]/div/div/div[1]/div[1]/div/div[5]/div/div[2]/button').click()
            except Exception:
                tinder.driver.find_element_by_xpath(xpath=f'//*[@id="{div_id}"]/div/div[1]/div/main/div[1]/div/div/div[1]/div[1]/div/div[4]/div/div[2]/button').click()
            finally:
                time.sleep(1)
        """</CODE FOR TINDER>"""

        # Display interim results, but with a carriage return at the end of the
        # line, so subsequent lines will overwrite them.
        #
        # If the previous result was longer than this one, we need to print
        # some extra spaces to overwrite the previous result
        overwrite_chars = " " * (num_chars_printed - len(transcript))

        if not result.is_final:
            sys.stdout.write(transcript + overwrite_chars + "\r")
            sys.stdout.flush()

            num_chars_printed = len(transcript)

        else:
            print(transcript + overwrite_chars)

            # Exit recognition if any of the transcribed phrases could be
            # one of our keywords.
            if re.search(r"\b(exit|quit)\b", transcript, re.I):
                print("Exiting..")
                break

            num_chars_printed = 0

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

def main():
    # See http://g.co/cloud/speech/docs/languages for a list of supported languages.

    # Create Tinder class and assign it to a variable
    global tinder 

    tinder = Tinder(url='https://tinder.com/app/recs',
                    driver_path=r'C:\Users\Alex\Desktop\Python drivers\chromedriver.exe'
                    )

    # Log in to Tinder
    tinder.log_in()

    # Get the div ID
    tinder.get_div_id()

    # Instantiate the speech client
    client = speech.SpeechClient()

    # Provide information to the recognizer, specifying how to process the request (general config)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code='en-US', # a BCP-47 language tag
    )

    # Provide information to the recognizer, specifying how to process the request (streaming config)
    streaming_config = speech.StreamingRecognitionConfig(
        config=config, 
        interim_results=True
    )

    with MicrophoneStream(rate=RATE, chunk=CHUNK) as stream:
        audio_generator = stream.generator()

        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in audio_generator
        )

        responses = client.streaming_recognize(config=streaming_config, 
                                               requests=requests
                                              )

        # Now, put the transcription responses to use.
        listen_print_loop(responses)

# Run the script
if __name__ == '__main__':
    time.sleep(2)
    main()
