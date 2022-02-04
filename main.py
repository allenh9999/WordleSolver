"""Runs the program."""

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import string
import time
import json
import random
from enum import Enum
from tkinter import Tk
import sys


class Letter(Enum):
    """Enumerator to classify each letter."""

    UNKNOWN = -1
    ZERO = 0
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    ABSENT = 5
    PRESENT = 6


def update_keys(driver, row, letters, present_list):
    """Update letters and present_list based on the current row."""
    time.sleep(2)
    row = driver.execute_script("return document.getElementsByTagName\
      ('game-app')[0].shadowRoot.getElementById('board')\
      .children[" + str(row) + "].shadowRoot.children[1]")
    row_letters = row.find_elements_by_tag_name("game-tile")
    total_correct = 0
    for idx, letter in enumerate(row_letters):
        char = letter.get_attribute("letter")
        if letter.get_attribute("evaluation") == "present":
            if char not in letters:
                letters[char] = Letter.PRESENT
                present_list[char] = {idx}
            elif letters[char] == Letter.PRESENT:
                present_list[char].add(idx)
        elif letter.get_attribute("evaluation") == "absent":
            if char in present_list:
                present_list[char].add(idx)
            else:
                present_list[char] = {idx}
            if char not in letters:
                letters[char] = Letter.ABSENT
        else:
            total_correct += 1
            letters[char] = Letter(idx)
    return total_correct == 5


def get_best_word(letters, words, present_list):
    """Get the best word from the letters, words, and present_list."""
    new_words = []
    must_have_chars, positional_chars, never_chars = set(), dict(), set()
    set_pos = set()
    # Set up the variables for faster access
    for letter, state in letters.items():
        if state == Letter.ABSENT:
            never_chars.add(letter)
        elif state == Letter.PRESENT:
            must_have_chars.add(letter)
        else:
            positional_chars[letter] = state.value
            set_pos.add(state.value)
    # create new_words
    for word in words:
        for char in present_list:
            if char not in word and char in must_have_chars:
                break
            for idx in present_list[char]:
                if word[idx] == char:
                    break
            else:
                continue
            break
        else:
            for char, idx in positional_chars.items():
                if word[idx] != char:
                    break
            else:
                for char in never_chars:
                    if char in word:
                        break
                else:
                    new_words.append(word)
    best_score, best_words = 0, []
    for word in new_words:
        score = 0
        for compare_word in new_words:
            # compare the two words, gives a score based on similarity
            for i in range(5):
                if word[i] == compare_word[i]:
                    score += 5 - len(positional_chars)
                elif i == word.find(word[i]):  # prevent duplicate letters
                    if compare_word.find(word[i]):
                        score += 1
        if score > best_score:
            best_score = score
            best_words = [word]
        elif score == best_score:
            best_words.append(word)
    return random.choice(best_words)


if __name__ == "__main__":
    # Get the driver for Selenium (requires Google Chrome
    driver = webdriver.Chrome(ChromeDriverManager().install())
    # Go to the Wordle website
    driver.get('https://www.powerlanguage.co.uk/wordle/')
    # Selenium doesn't allow you to access shadow roots, so you have to do
    #   this instead :)
    # Click the close icon
    close_icon = driver.execute_script("return document.getElementsByTagName\
      ('game-app')[0].shadowRoot.getElementById('game')\
      .getElementsByTagName('game-modal')[0].shadowRoot.children[1]\
      .getElementsByClassName('close-icon')[0]")
    close_icon.click()
    # Initialize the lists
    letters, words, present_list = {}, json.load(open("words.json")), {}
    # Guess words until there are no more guesses/you guess the word
    win = False
    for i in range(6):
        # Send the guessed word to the driver
        if i == 0:
            driver.find_element_by_tag_name('body').send_keys("slate\n")
        else:
            driver.find_element_by_tag_name('body').send_keys(
                get_best_word(letters, words, present_list) + "\n")
        # Update the letters and present list
        if update_keys(driver, i, letters, present_list):
            win = True
            break
    if win:
        # Send the clipboard output to stdout or an outfile (if specified)
        time.sleep(4)
        share_btn = driver.execute_script("return document.\
          getElementsByTagName('game-app')[0].shadowRoot.\
          getElementById('game').getElementsByTagName\
          ('game-stats')[0].shadowRoot\
          .getElementById('share-button')")
        share_btn.click()
        app = Tk()
        if len(sys.argv) == 2:
            open(sys.argv[1], 'w').write(app.clipboard_get())
        else:
            print(app.clipboard_get())
        app.destroy()
