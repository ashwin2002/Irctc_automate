'''
    GPL License:

    Irctc_automate is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Irctc_automate is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Irctc_automate.  If not, see <http://www.gnu.org/licenses/>.
'''

from time import sleep
import SendKeys

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

class WebAutomation:
    def logger (self, level, message):
        print level + ': ' + message
        return

    def waitForXPathToLoad (self, expectedXPath, timeoutVal):
        try:
            reqObj  = WebDriverWait (self.browserDriver, timeoutVal)
            if reqObj:
                reqObj  = reqObj.until (EC.presence_of_element_located((By.XPATH, expectedXPath)))
        except Exception:
            self.logger ('WARNING', "'" + expectedXPath + "' not present")
            reqObj = None

        if reqObj:
            while True:
                if reqObj.is_enabled():
                    break
        return reqObj

    def waitForXPathAndSendKeys (self, expectedXPath, dataToType, pressEnterFlag, timeoutVal):
        xpathObj = self.waitForXPathToLoad (expectedXPath, timeoutVal)
        if xpathObj:
            xpathObj.send_keys (dataToType)
            if pressEnterFlag:
                sleep (1)
                #SendKeys.SendKeys ("{ENTER}")
                xpathObj.send_keys (Keys.RETURN)
        return

    def waitForXPathAndClick (self, expectedXPath, timeoutVal):
        xpathObj = self.waitForXPathToLoad (expectedXPath, timeoutVal)
        if xpathObj:
            xpathObj.click ()
        return

    def selectDropDownOption (self, selectHtmlObj, valToSelect, valIsInteger):
        isValueSelected = False

        if not(valIsInteger in [True, False]):
            self.logger ('ERROR', "Non boolean value provided for 'valIsInteger'")
            return isValueSelected

        availableOptionTags = selectHtmlObj.find_elements_by_tag_name ('option')
        for optionTag in availableOptionTags:
            optionVal = optionTag.get_attribute ('value')
            optionTxt = ((optionTag.text).lower()).strip ()
            if valIsInteger:
                try:
                    optionVal = int(optionVal)
                    optionTxt = int(optionTxt)
                    valToSelect = int(valToSelect)
                except:
                    continue
            if (valIsInteger) and (valToSelect == optionTxt) and (valToSelect == optionVal):
                optionTag.click ()
                isValueSelected = True
                break
            elif (valIsInteger == False) and (optionTxt == valToSelect):
                optionTag.click ()
                isValueSelected = True
                break

        return isValueSelected

    def startBrowser (self, browserType):
        if browserType == 'firefox':
            self.browserDriver = webdriver.Firefox ()
            self.browserDriver.maximize_window ()
        else:
            self.logger ('ERROR', "Browser '"+ browserType + "' not supported")
        return

    def closeBrowser (self):
        if self.browserDriver:
            #self.browserDriver.quit()
            self.logger ('WARNING', 'Please close the browser yourself')
            pass
        return

    def openUrl (self, url):
        self.browserDriver.get (url)
        return
