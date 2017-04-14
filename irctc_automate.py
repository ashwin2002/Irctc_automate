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

import sys, traceback
import re, configparser
import SendKeys

from optparse import OptionParser
from WebAutomation import WebAutomation
from OnlinePayment import OnlinePayment

def logger (logLevel, logMessage):
    print logLevel + ": " + logMessage
    return

def isConfigDataValid (bookingInfoConfig):
    isValid = True
    requiredConfigSections  = ['TIMEOUT', 'ACCOUNTS', 'JOURNEY', 'PASSENGERS', 'CHILDREN']
    validPassengerKeys      = ['passenger1', 'passenger2', 'passenger3', 'passenger4', 'passenger5', 'passenger6']
    validChildrenKeys       = ['child1', 'child2']

    for reqSection in requiredConfigSections:
        if not(reqSection in bookingInfoConfig):
            logger ('ERROR', "Config section '" + reqSection + "' missing in config.ini file")
            isValid = False

    if not(sys.argv[1] in bookingInfoConfig['ACCOUNTS'].keys()):
        logger('ERROR', "Login details missing for userid '" + sys.argv[1] + "'")
        isValid = False

    for journeyData in bookingInfoConfig['JOURNEY'].keys():
        if bookingInfoConfig['JOURNEY'][journeyData] == '':
            logger ('ERROR', "Journey data '" + journeyData + "' is empty")
            isValid = False

    noOfPassengers = len(bookingInfoConfig['PASSENGERS'].keys())
    noOfChildren   = len(bookingInfoConfig['CHILDREN'].keys())
    if noOfPassengers < 1 and noOfPassengers > 6:
        logger ('ERROR', "Please provide only 1 - 6 passenger info")

    if noOfChildren < 1 and noOfChildren > 2:
        logger ('ERROR', "Please provide only 1 - 2 children info")

    for passengerkey in bookingInfoConfig['PASSENGERS'].keys():
        if not(passengerkey in validPassengerKeys):
            logger ('ERROR', "Invalid passenger key '" + passengerkey + "'")
            isValid = False
        elif len(bookingInfoConfig['PASSENGERS'][passengerkey].split(';')) != 7:
            logger ('ERROR', "Please provide the '" + passengerkey + "' deatils as name;age;gender;berth_preference;is_senior_citizen;nationality;id_card_no")

    for passengerkey in bookingInfoConfig['CHILDREN'].keys():
        if not(passengerkey in validChildrenKeys):
            logger ('ERROR', "Invalid child key '" + passengerkey + "'")
            isValid = False
        elif len(bookingInfoConfig['CHILDREN'][passengerkey].split(';')) != 3:
            logger ('ERROR', "Please provide the '" + passengerkey + "' deatils as name;age;gender")

    return isValid

class Irctc (WebAutomation):
    timeoutVal              = 0
    browserDriver           = None
    bookingInfoConfigData   = None
    xpathConfigData         = None
    errorCondition          = False
    __journeyDate           = None

    def __init__ (self, configData):
        logger ('INFO', "Initializing '" + self.__class__.__name__ + "' object")
        self.bookingInfoConfigData = configData
        self.timeoutVal         = int(self.bookingInfoConfigData['TIMEOUT']['timeout'])
        self.errorCondition     = False
        self.xpathConfigData    = configparser.ConfigParser(); 
        self.xpathConfigData.read ('xpath_irctc.ini')
        return

    def destroy (self):
        logger ('INFO', "Destroying '" + self.__class__.__name__ + "' object")
        self.browserDriver = None
        del self
        return

    def printTrainData (self, tNo, tName, tStartsFrom, tEndsAt, tDepTime, tArrivalTime, tTravelDist, tTravelTime):
        logger ('INFO', "############ Train details for '" + tNo + "' ############")
        logger ('INFO', "Train Name          '" + tName + "'")
        logger ('INFO', "Starting Station    '" + tStartsFrom + "'")
        logger ('INFO', "Terminating Station '" + tEndsAt + "'")
        logger ('INFO', "Departure time      '" + tDepTime + "'")
        logger ('INFO', "Arrival time        '" + tArrivalTime + "'")
        logger ('INFO', "Distance travelled  '" + tTravelDist + "'")
        logger ('INFO', "Travel Time         '" + tTravelTime + "'")
        return

    def irctcLogin (self):
        loginProcedureComplete  = False
        while not(loginProcedureComplete):
            self.waitForXPathAndSendKeys (self.xpathConfigData['LOGIN']['userName'], sys.argv[1], False, self.timeoutVal + 60)
            self.waitForXPathAndSendKeys (self.xpathConfigData['LOGIN']['password'], self.bookingInfoConfigData['ACCOUNTS'][sys.argv[1]], False, self.timeoutVal)
            self.waitForXPathAndClick (self.xpathConfigData['LOGIN']['captcha'], self.timeoutVal)
            raw_input ('Enter Captcha and press \'Enter\' key..')
            SendKeys.SendKeys ("%{TAB}")

            self.waitForXPathAndClick (self.xpathConfigData['LOGIN']['loginBtn'], self.timeoutVal)

            loginErrTxt  = self.waitForXPathToLoad (self.xpathConfigData['LOGIN']['invalidLoginErrorTxt'], 5)
            if loginErrTxt:
                invalidLoginPopUpOkBtn  = self.waitForXPathToLoad (self.xpathConfigData['LOGIN']['invalidLoginErrorOkBtn'], 1)
                errorStatusRegexp       = re.match ('invalid captcha', loginErrTxt.text, re.I)
                if errorStatusRegexp:
                    invalidLoginPopUpOkBtn.click()
                    logger ('ERROR', "Invalid Captcha entered!")
                else:
                    errorStatusRegexp = re.match ('wrong credentials', loginErrTxt.text, re.I)
                    if errorStatusRegexp:
                        invalidLoginPopUpOkBtn.click()
                        logger ('ERROR', "Invalid Login credentials!")
                        self.errorCondition = True
                    else:
                        errorStatusRegexp = re.match ('invalid user', loginErrTxt.text, re.I)
                        if errorStatusRegexp:
                            invalidLoginPopUpOkBtn.click()
                            logger ('ERROR', "Invalid user name")
                            self.errorCondition = True
            else:
                self.waitForXPathAndClick (self.xpathConfigData['LOGIN']['oldSessionInvalidate'], 1)
                loginProcedureComplete = True

            if self.errorCondition:
                loginProcedureComplete = True
        return

    def fillPlanMyJourneyDetails (self):
        if self.errorCondition:
            return

        fromStnXPath                = self.xpathConfigData['JOURNEYPLANNER']['fromStn']
        toStnXPath                  = self.xpathConfigData['JOURNEYPLANNER']['toStn']
        journeyDateXPath            = self.xpathConfigData['JOURNEYPLANNER']['journeyDate']
        journeySelectSubmitBtnXPath = self.xpathConfigData['JOURNEYPLANNER']['journeySelectSubmitBtn']

        fromStn     = self.bookingInfoConfigData['JOURNEY']['from']
        toStn       = self.bookingInfoConfigData['JOURNEY']['to']

        self.waitForXPathAndSendKeys (fromStnXPath, fromStn, True, self.timeoutVal + 60)
        self.waitForXPathAndSendKeys (toStnXPath, toStn, True, self.timeoutVal)
        self.waitForXPathAndSendKeys (journeyDateXPath, self.__journeyDate, False, self.timeoutVal)
        self.waitForXPathAndClick (journeySelectSubmitBtnXPath, self.timeoutVal)
        dateNotInResevationPeriodObj = self.waitForXPathToLoad (self.xpathConfigData['JOURNEYPLANNER']['journeyDateNotInResevationPeriodTxt'], 5)
        if dateNotInResevationPeriodObj:
            self.errorCondition = True
            logger ('ERROR', "Journey date '" + self.__journeyDate + "' not in reservation period")
        else:
            reservationNotAllowedObj = self.waitForXPathToLoad (self.xpathConfigData['JOURNEYPLANNER']['onlineBookingNotAllowedNow'], 1)
            if reservationNotAllowedObj:
                if re.match ('please try after', reservationNotAllowedObj.text, re.I):
                    logger ('ERROR', reservationNotAllowedObj.text);
                    self.errorCondition = True
        return

    def selectTrainAndBerth (self):
        if self.errorCondition:
            return

        trainFound  = False
        berthFound  = False
        reqQuota    = self.bookingInfoConfigData['JOURNEY']['quota']
        reqClass    = (self.bookingInfoConfigData['JOURNEY']['class']).upper()
        trainNo     = self.bookingInfoConfigData['JOURNEY']['trainNumber']

        self.waitForXPathAndClick (self.xpathConfigData['QUOTATYPE'][reqQuota], self.timeoutVal + 60)
        availableTrainDetailsTbl = (self.browserDriver).find_element_by_xpath(self.xpathConfigData['TRAINBERTHSELECT']['trainListTbl'])
        for currTrainDetailRowElement in availableTrainDetailsTbl.find_elements_by_tag_name("tr"):
            if (currTrainDetailRowElement.find_element_by_tag_name('a').text) == trainNo:
                trainFound = True
                targetTblRowDataNode = currTrainDetailRowElement.find_elements_by_tag_name ('td')
                trainName        = targetTblRowDataNode[1].text
                trainStartsFrom  = targetTblRowDataNode[2].text
                trainEndsAt      = targetTblRowDataNode[4].text
                trainDepTime     = targetTblRowDataNode[3].text
                trainArrivalTime = targetTblRowDataNode[5].text
                trainTravelDist  = targetTblRowDataNode[6].text
                trainTravelTime  = targetTblRowDataNode[7].text

                self.printTrainData (trainNo, trainName, trainStartsFrom, trainEndsAt, trainDepTime, trainArrivalTime, trainTravelDist, trainTravelTime)

                targetTblRowDataNode = targetTblRowDataNode[len(targetTblRowDataNode) - 1]
                availableClassList   = targetTblRowDataNode.find_elements_by_tag_name ("a")
                for availableClass in availableClassList:
                    if availableClass.text == reqClass:
                        berthFound = True
                        availableClass.click()
                        self.waitForXPathToLoad (self.xpathConfigData['TRAINBERTHSELECT']['trainBookNow'], self.timeoutVal)
                        statusNode  = self.browserDriver.find_element_by_xpath(self.xpathConfigData['TRAINBERTHSELECT']['trainBookNow'])
                        currStatus  = ((statusNode.text).replace("Book Now","")).strip()
                        try:
                            bookNowLink = statusNode.find_element_by_tag_name('a')
                        except NoSuchElementException, e:
                            logger ('ERROR', "Book now link not present")

                        currStatusTextExtract = re.match ('available-([0-9]+)(#?)', currStatus,re.I)
                        print " Current status: " + currStatus
                        if currStatusTextExtract:
                            if currStatusTextExtract.group(2) == "#":
                                logger ('INFO', "Booking not opened for '" + trainNo + "' and quota '" + quota + "'")
                            else:
                                bookTrainFlag = True
                        else:
                            SendKeys.SendKeys ("%{TAB}")
                            while True:
                                userOption = (raw_input(" Proceed to booking ? (y/n) ")).lower()
                                if userOption == 'y':
                                    bookTrainFlag = True
                                    break
                                elif userOption == 'n':
                                    bookTrainFlag = False
                                    break
                                else:
                                    continue
                            SendKeys.SendKeys ("%{TAB}")

                        if bookTrainFlag:
                            bookNowLink.click ()
                            self.waitForXPathAndClick (self.xpathConfigData['TRAINBERTHSELECT']['trainBookingContWithPrevChoice'], 10)
                        else:
                            logger ('INFO', "Unable to book the requested train !")
                if not(berthFound):
                    logger ('ERROR', "Requested berth '" + reqBerthClass + "' not available in this train")

            if trainFound:
                break

        if not(trainFound):
            logger ('ERROR', "Requested train '" + trainNo + "' not available on '" + self.__journeyDate + "'")
        return

    def enterPassengerDetails (self):
        if self.errorCondition:
            return

        isCaptchaInvalid  = True
        passengerInfoList = []
        passengerInfoList.append (self.bookingInfoConfigData['PASSENGERS']['passenger1'].split(';'))
        passengerInfoList.append (self.bookingInfoConfigData['PASSENGERS']['passenger2'].split(';'))
        passengerInfoList.append (self.bookingInfoConfigData['PASSENGERS']['passenger3'].split(';'))
        passengerInfoList.append (self.bookingInfoConfigData['PASSENGERS']['passenger4'].split(';'))
        passengerInfoList.append (self.bookingInfoConfigData['PASSENGERS']['passenger5'].split(';'))
        passengerInfoList.append (self.bookingInfoConfigData['PASSENGERS']['passenger6'].split(';'))

        passengerIndex = 1
        for passengerInfo in passengerInfoList:
            passengerInfo[0] = passengerInfo[0].strip()
            if passengerInfo[0] != "":
                passengerInfo[1] = passengerInfo[1].strip()
                passengerInfo[2] = (passengerInfo[2].strip()).lower()
                passengerInfo[3] = (passengerInfo[3].strip()).lower()
                passengerInfo[4] = (passengerInfo[4].strip()).lower()
                passengerInfo[5] = passengerInfo[5].strip()
                passengerInfo[6] = passengerInfo[6].strip()

                self.waitForXPathAndSendKeys (self.xpathConfigData['PASSENGER'+str(passengerIndex)]['name'], passengerInfo[0], False, self.timeoutVal + 60)
                self.waitForXPathAndSendKeys (self.xpathConfigData['PASSENGER'+str(passengerIndex)]['age'], passengerInfo[1], False, self.timeoutVal)

                genderSelectObj  = self.waitForXPathToLoad (self.xpathConfigData['PASSENGER'+str(passengerIndex)]['gender'], self.timeoutVal)
                if genderSelectObj:
                    self.selectDropDownOption (genderSelectObj, passengerInfo[2], False)

                berthPreferenceSelectObj = self.waitForXPathToLoad (self.xpathConfigData['PASSENGER'+str(passengerIndex)]['berthPreference'], self.timeoutVal)
                if berthPreferenceSelectObj:
                    self.selectDropDownOption (berthPreferenceSelectObj, passengerInfo[3], False)

                if passengerInfo[4] in ['y', 'yes']:
                    self.waitForXPathAndClick (self.xpathConfigData['PASSENGER'+str(passengerIndex)]['isSeniorCitizen'], self.timeoutVal)

                #self.waitForXPathAndSendKeys (self.xpathConfigData['PASSENGER'+str(passengerIndex)]['nationality], passengerInfo[5], False, self.timeoutVal)
                self.waitForXPathAndSendKeys (self.xpathConfigData['PASSENGER'+str(passengerIndex)]['idCardNo'], passengerInfo[6], False, self.timeoutVal)
                passengerIndex += 1

        passengerInfoList = []
        passengerInfoList.append (self.bookingInfoConfigData['CHILDREN']['child1'].split(';'))
        passengerInfoList.append (self.bookingInfoConfigData['CHILDREN']['child2'].split(';'))

        passengerIndex = 1
        for passengerInfo in passengerInfoList:
            passengerInfo[0] = passengerInfo[0].strip()
            if passengerInfo[0] != "":
                passengerInfo[1] = (passengerInfo[1].strip()).lower()
                passengerInfo[2] = passengerInfo[1].strip()

                if passengerInfo[1] == '0':
                    self.waitForXPathAndClick (self.xpathConfigData['CHILD'+str(passengerIndex)]['age0'], self.timeoutVal)
                elif passengerInfo[1] == '1':
                    self.waitForXPathAndClick (self.xpathConfigData['CHILD'+str(passengerIndex)]['age1'], self.timeoutVal)
                elif passengerInfo[2] == '2':
                    self.waitForXPathAndClick (self.xpathConfigData['CHILD'+str(passengerIndex)]['age2'], self.timeoutVal)
                elif passengerInfo[3] == '3':
                    self.waitForXPathAndClick (self.xpathConfigData['CHILD'+str(passengerIndex)]['age3'], self.timeoutVal)
                elif passengerInfo[4] == '4':
                    self.waitForXPathAndClick (self.xpathConfigData['CHILD'+str(passengerIndex)]['age4'], self.timeoutVal)

                if passengerInfo[2] == 'm' or passengerInfo[2] == 'male':
                    self.waitForXPathAndClick (self.xpathConfigData['CHILD'+str(passengerIndex)]['genderM'], self.timeoutVal)
                elif passengerInfo[2] == 'f' or passengerInfo[2] == 'female':
                    self.waitForXPathAndClick (self.xpathConfigData['CHILD'+str(passengerIndex)]['genderF'], self.timeoutVal)
                passengerIndex += 1

        considerAutoUpgrade = (self.bookingInfoConfigData['JOURNEY']['considerAutoUpgrade']).lower()
        smsPhoneNo          = self.bookingInfoConfigData['JOURNEY']['phoneNumForSMS']

        self.waitForXPathAndClick (self.xpathConfigData['PASSENGERINFO']['smsPhoneNo'], self.timeoutVal)
        if smsPhoneNo != 'default':
            self.waitForXPathAndSendKeys (self.xpathConfigData['PASSENGERINFO']['smsPhoneNo'], smsPhoneNo, False, self.timeoutVal)

        if considerAutoUpgrade in ['y', 'yes']:
            self.waitForXPathAndClick (self.xpathConfigData['PASSENGERINFO']['considerAutoUpgradation'], self.timeoutVal)

        while isCaptchaInvalid:
            tatkalTimeCaptchaTxtObj = self.waitForXPathToLoad (self.xpathConfigData['PASSENGERINFO']['passengerInfoCaptcha'], 2)
            if tatkalTimeCaptchaTxtObj:
                tatkalTimeCaptchaTxtObj.click ()
            else:
                flashCaptchaObj     = self.waitForXPathToLoad (self.xpathConfigData['PASSENGERINFO']['passengerInfoClickCaptcha'], 1)
                if flashCaptchaObj:
                    pass
                else:
                    self.waitForXPathAndClick (self.xpathConfigData['PASSENGERINFO']['passengerInfoImgCaptcha'], self.timeoutVal)

            raw_input ("Enter Captcha and press 'Enter' key..")
            SendKeys.SendKeys ("%{TAB}")
            self.waitForXPathAndClick (self.xpathConfigData['PASSENGERINFO']['passengerDetailsNextBtn'], self.timeoutVal)

            invalidCaptchaTxtObj = self.waitForXPathToLoad (self.xpathConfigData['PASSENGERINFO']['invalidCaptchaEntered'], 5)
            if not(invalidCaptchaTxtObj):
                isCaptchaInvalid = False

        return

    def selectPaymentOption (self):
        if self.errorCondition:
            return

        isBankSelected = False
        fullPaymentListDivBlock = None
        userPaymentMode = (self.bookingInfoConfigData['PAYMENT']['mode']).lower()
        userBankName    = self.bookingInfoConfigData['PAYMENT']['bankName']
        self.waitForXPathAndClick (self.xpathConfigData['PAYMENTOPTIONS'][userPaymentMode], self.timeoutVal + 60)

        fullPaymentListBlock = self.waitForXPathToLoad (self.xpathConfigData['PAYMENTOPTIONS'][userPaymentMode+'Tbl'], self.timeoutVal)
        if fullPaymentListBlock:
            availableBankingGateways = fullPaymentListBlock.find_elements_by_tag_name ('td')

        for tdTag in availableBankingGateways:
            inputTag        = tdTag.find_element_by_tag_name ('input')
            if inputTag:
                currPaymentMode = (inputTag.get_attribute('id')).lower()
                currBankName    = (tdTag.text).strip()
            else:
                continue

            if (currPaymentMode == userPaymentMode) and (currBankName == userBankName):
                inputTag.click ()
                self.waitForXPathAndClick (self.xpathConfigData['PAYMENTOPTIONS']['makePaymentBtn'], self.timeoutVal)
                isBankSelected = True
                break

        if not(isBankSelected):
            logger ('WARNING', "Unable to select payment method")
            self.errorCondition = True

        return

    def makePayment (self):
        if self.errorCondition:
            return

        paymentObj = OnlinePayment (self, self.bookingInfoConfigData, self.xpathConfigData)
        isPaymentFailure = paymentObj.pay ()
        del paymentObj

        if isPaymentFailure:
            self.errorCondition = True

        return

    def bookTicket (self, journeyDate):
        self.__journeyDate = journeyDate
        self.startBrowser ('firefox')
        self.openUrl (self.bookingInfoConfigData['URL']['url'])
        self.irctcLogin ()
        self.fillPlanMyJourneyDetails ()
        self.selectTrainAndBerth ()
        self.enterPassengerDetails ()
        self.selectPaymentOption ()
        paymentFailure = self.makePayment ()
        if paymentFailure:
            self.errorCondition = True

        raw_input ("Please press 'Enter' after booking comfirmation ..")
        self.closeBrowser()
        return

    def cancelTicket (self, pnrNum):
        logger ('WARNING', 'Not yet implemented')
        return

    def ticketStatus (self, pnrNum):
        logger ('WARNING', 'Not yet implemented')
        return

if __name__ == '__main__':
    cmdLineArgParser = OptionParser()
    cmdLineArgParser.add_option ('-d', '--date', dest = 'journeyDate', help = 'Use this DATE for ticket booking', metavar = 'DATE', action = 'store')
    cmdLineArgParser.add_option ('--pnr', dest = 'pnrNum', help = 'User this PNR_NUMBER for cancel or status enquiry', metavar = 'PNR_NUMBER', action = 'store')
    (options, args) = cmdLineArgParser.parse_args()

    validActionList = ['book', 'cancel', 'status']
    if len(args) != 3 or not(args[2] in validActionList):
        print ""
        print " Usage: " + sys.argv[0] + " irctcUserId profileFile "+ '|'.join(validActionList) + " [options]"
        print ""
        exit (0)

    bookingInfoConfig = configparser.ConfigParser ()
    bookingInfoConfig.read (args[1])

    try:
      if isConfigDataValid (bookingInfoConfig):
        myIrctcObj = Irctc (bookingInfoConfig)

        if args[2] == 'book' and getattr (options, 'journeyDate'):
            myIrctcObj.bookTicket (getattr(options, 'journeyDate'))
        elif args[2] == 'cancel' and getattr (options, 'pnrNum'):
            myIrctcObj.cancelTicket (getattr(options, 'pnrNum'))
        elif args[2] == 'status' and getattr (options, 'pnrNum'):
            myIrctcObj.ticketStatus (getattr (options, 'pnrNum'))
        else:
            logger ('ERROR', "Please provide proper options for '" + args[2] + "'");

        myIrctcObj.destroy ()
    except Exception:
        print (traceback.format_exc())

    exit (0)
