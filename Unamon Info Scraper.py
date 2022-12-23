import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QTextEdit
import requests
from bs4 import BeautifulSoup

class UnamonInfoGUI(QWidget):
  def __init__(self):
    super().__init__()

    # Set up the UI
    self.name_label = QLabel("Unamon Name:")
    self.name_edit = QLineEdit()
    self.info_button = QPushButton("Get Info")
    self.info_edit = QTextEdit()

    layout = QVBoxLayout()
    layout.addWidget(self.name_label)
    layout.addWidget(self.name_edit)
    layout.addWidget(self.info_button)
    layout.addWidget(self.info_edit)
    self.setLayout(layout)

    # Connect the button to the get_info function
    self.info_button.clicked.connect(self.get_info)
    self.name_edit.returnPressed.connect(self.get_info)

  def get_unamon_info(self, name):
    # Replace spaces in the Unamon's name with underscores, as that's how the name is formatted in the URL
    name = name.replace(" ", "_")

    # Make a request to the UNA Wiki page for the Unamon
    url = f"https://welcometouna.fandom.com/wiki/{name}"
    response = requests.get(url)

    # Parse the HTML of the page
    soup = BeautifulSoup(response.text, "html.parser")

    # Find all elements with the class "pi-data-value pi-font"
    infobox_values = soup.find_all(class_="pi-data-value pi-font")

    # Find all elements with the class "pi-data-label pi-secondary-font"
    infobox_labels = soup.find_all(class_="pi-data-label pi-secondary-font")

    # Zip the labels and values together into a list of tuples
    infobox_items = list(zip(infobox_labels, infobox_values))

    # Extract the text from each label and value, and add "Type" if the label is a sole number
    infobox_text = "\n".join([f"{label.get_text()}: {value.get_text()}" if not label.get_text().isdigit() else f"Type {label.get_text()}: {value.get_text()}" for label, value in infobox_items])

    # Remove any blank lines from the text
    infobox_text = "\n".join([line for line in infobox_text.split("\n") if line.strip() != ""])

    return infobox_text

  def get_info(self):
    # Get the name from the name edit field
    name = self.name_edit.text()

    # Get the infobox information
    infobox_text = self.get_unamon_info(name)

    # Check if the infobox text is empty
    if len(infobox_text) == 0:
      # Set the text of the info edit to a message indicating that the Unamon does not exist
      self.info_edit.setPlainText("Unamon does not exist.")
    else:
      # Set the infobox text as the text of the info edit
      self.info_edit.setPlainText(infobox_text)



# Run the GUI
app = QApplication(sys.argv)
gui = UnamonInfoGUI()
gui.show()
sys.exit(app.exec_())
