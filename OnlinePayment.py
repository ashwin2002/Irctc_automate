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

class OnlinePayment ():
    __parentClassObj    = None
    __profileConfigData = None
    __xpathConfigObj    = None
    timeoutVal          = 0

    def __init__ (self, parentObj, configParserObj, xpathConfigObj):
        self.__parentClassObj    = parentObj
        self.__profileConfigData = configParserObj
        self.__xpathConfigObj    = xpathConfigObj
        self.timeoutVal          = self.__parentClassObj.timeoutVal
        return

    def logger (self, level, message):
        print level + ': ' + message
        return

    def __validateCardNumber (self):
        isCardNumValid = True

        userCardNum = self.__profileConfigData['PAYMENT']['cardNumber']
        userCardNum = userCardNum.replace (' ', '')
        userCardNum = userCardNum.replace ('-', '')

        if len(userCardNum) != 16:
            isCardNumValid = False

        if isCardNumValid:
            userCardNum = [userCardNum[0:4], userCardNum[4:8], userCardNum[8:12], userCardNum[12:16]]
        else:
            userCardNum = None

        return userCardNum

    def __payWithCitibankGw (self):
        paymentFailure = False

        #### Enter Card detail Step ####

        if self.__profileConfigData['PAYMENT']['cardType'] == 'citibank':
            targetCardTypeRadio = self.__xpathConfigObj['CITIBANKPAYMENTGW']['citiBankCard']
            targetCardNumBox1   = self.__xpathConfigObj['CITIBANKPAYMENTGW']['citiBankCardNumBox1']
            targetCardNumBox2   = self.__xpathConfigObj['CITIBANKPAYMENTGW']['citiBankCardNumBox2']
            targetCardNumBox3   = self.__xpathConfigObj['CITIBANKPAYMENTGW']['citiBankCardNumBox3']
            targetCardNumBox4   = self.__xpathConfigObj['CITIBANKPAYMENTGW']['citiBankCardNumBox4']
        else:
            targetCardTypeRadio = self.__xpathConfigObj['CITIBANKPAYMENTGW']['otherBankCard']
            targetCardNumBox1   = self.__xpathConfigObj['CITIBANKPAYMENTGW']['citiBankCardNumBox1']
            targetCardNumBox2   = self.__xpathConfigObj['CITIBANKPAYMENTGW']['citiBankCardNumBox2']
            targetCardNumBox3   = self.__xpathConfigObj['CITIBANKPAYMENTGW']['citiBankCardNumBox3']
            targetCardNumBox4   = self.__xpathConfigObj['CITIBANKPAYMENTGW']['citiBankCardNumBox4']

        userCardNum = self.__validateCardNumber ()
        if userCardNum:
            self.__parentClassObj.waitForXPathAndClick (targetCardTypeRadio, self.timeoutVal + 60)
            self.__parentClassObj.waitForXPathAndSendKeys (targetCardNumBox1, userCardNum[0], False, self.timeoutVal)
            self.__parentClassObj.waitForXPathAndSendKeys (targetCardNumBox2, userCardNum[1], False, self.timeoutVal)
            self.__parentClassObj.waitForXPathAndSendKeys (targetCardNumBox3, userCardNum[2], False, self.timeoutVal)
            self.__parentClassObj.waitForXPathAndSendKeys (targetCardNumBox4, userCardNum[3], False, self.timeoutVal)
        else:
            paymentFailure = True

        if not(paymentFailure):
            selectObj       = self.__parentClassObj.waitForXPathToLoad (self.__xpathConfigObj['CITIBANKPAYMENTGW']['citiBankCardExpiryMonth'], self.timeoutVal)
            valueToSelect   = self.__profileConfigData['PAYMENT']['cardExpiryMonth']
            isValueSelected = self.__parentClassObj.selectDropDownOption (selectObj, valueToSelect, True)
            if not(isValueSelected):
                paymentFailure = True

            selectObj       = self.__parentClassObj.waitForXPathToLoad (self.__xpathConfigObj['CITIBANKPAYMENTGW']['citiBankCardExpiryYear'], self.timeoutVal)
            valueToSelect   = self.__profileConfigData['PAYMENT']['cardExpiryYear']
            isValueSelected = self.__parentClassObj.selectDropDownOption (selectObj, valueToSelect, True)
            if not(isValueSelected):
                paymentFailure = True

        if not(paymentFailure):
            self.__parentClassObj.waitForXPathAndSendKeys (self.__xpathConfigObj['CITIBANKPAYMENTGW']['citiBankCardCvvCode'], self.__profileConfigData['PAYMENT']['cardCvvCode'], False, self.timeoutVal)
            self.__parentClassObj.waitForXPathAndClick (self.__xpathConfigObj['CITIBANKPAYMENTGW']['citiBankCardSubmitBtn'], self.timeoutVal)

        #### Pin / OTP verfication step ####
        userVerifyType = (self.__profileConfigData['PAYMENT']['verifyType']).lower()
        userIpinVal    = (self.__profileConfigData['PAYMENT']['ipinVal']).lower()
        if userVerifyType == 'ipin':
            targetPaymentModeSelectObj = self.__xpathConfigObj['CITIBANKPAYMENTGW']['selectIpinMethod']
        elif userVerifyType == 'otp':
            targetPaymentModeSelectObj = self.__xpathConfigObj['CITIBANKPAYMENTGW']['selectOtpMethod']
        else:
            paymentFailure = True

        if not(paymentFailure):
            self.__parentClassObj.waitForXPathAndClick (targetPaymentModeSelectObj, self.timeoutVal + 60)
            if userVerifyType == 'ipin':
                if userIpinVal != '':
                    ipinInputTxtObj = self.__xpathConfigObj['CITIBANKPAYMENTGW']['citiBankIpinInput']
                    if ipinInputTxtObj:
                        self.__parentClassObj.waitForXPathAndSendKeys (ipinInputTxtObj, userIpinVal, False, self.timeoutVal)
                        self.__parentClassObj.waitForXPathAndClick (self.__xpathConfigObj['CITIBANKPAYMENTGW']['citiBankNextBtn'], self.timeoutVal)
                    else:
                        payementFailure = True
                else:
                    self.logger ('INFO', 'Please complete the I-PIN verification to complete the transaction')
            elif userVerifyType == 'otp':
                self.logger ('INFO', 'Please enter OTP to complete the transaction')

        return paymentFailure

    def pay (self):
        paymentFailure = False

        if self.__profileConfigData['PAYMENT']['gateway'] == 'citibank':
            paymentFailure = self.__payWithCitibankGw ()
        else:
            paymentFailure = True
            self.__logger ('ERROR', 'Payment gateway not supported currently !')
        return paymentFailure
