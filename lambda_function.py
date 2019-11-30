# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
import logging
from random import randint

import ask_sdk_core.utils as ask_utils

import requests
import json
from datetime import datetime

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_request_type, is_intent_name

from ask_sdk_model import Response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class WarframeAPIQuery():

    @staticmethod
    def grabStatus():
        url = "https://api.warframestat.us/pc/" + "cetusCycle"
        response = requests.get(url)
        if response.status_code == 200:
            parsed_json = json.loads(response.text)
            is_day = parsed_json['isDay']
            if is_day:
                return "It is currently daytime. Praise the Void!"
            else:
                return "It is night. The Void pulses with anticipation!"
        else:
            return "Error grabbing API"



    @staticmethod
    def current_arbitration():
        url = "https://api.warframestat.us/pc/" + "arbitration"
        response = requests.get(url)
        if response.status_code == 200:
            parsed_json = json.loads(response.text)
            expiry = parsed_json['expiry']
            datetime_object = datetime.strptime(expiry, '%Y-%m-%dT%H:%M:%S.000Z')
            diff = datetime.now() - datetime_object

            # I got one response that was:
            #{"activation":"2019-11-30T16:05:00.000Z","expiry":"2019-11-30T17:05:00.000Z","solnode":"SolNode308","node":"undefined (undefined)","type":"Disruption"}
            # So handling that bug as gracefully as I can

            if 'enemy' in parsed_json:
                enemy = parsed_json['enemy']
            else:
                enemy = ""

            type = parsed_json['type']

            if enemy == "Grineer":
                enemy= "<sub alias=\"grah near\">Grineer</sub>"

            if diff.total_seconds() > 0:
                return "I'm not sure what the current Arbitration is - The API hasn't updated to the new one yet. But, the old one was " + enemy + " " + type + "."

            return "The current Arbitration is " + enemy + " " + type + "."
        else:
            return "Error grabbing API"

    @staticmethod
    def cetus_time():
        url = "https://api.warframestat.us/pc/" + "cetusCycle"
        response = requests.get(url)
        if response.status_code == 200:
            parsed_json = json.loads(response.text)
            is_day = parsed_json['isDay']
            time_remaining = parsed_json['timeLeft']

            constructed_time = ""
            if time_remaining.find('h') == -1:
                constructed_time = "0h " + time_remaining

            if time_remaining.find('s') == -1:
                constructed_time = constructed_time + "0s"

            if time_remaining.find('m') == -1:
                datetime_object = datetime.strptime(constructed_time, '%Hh %Ss')
            else:
                datetime_object = datetime.strptime(constructed_time, '%Hh %Mm %Ss')

            min_remaining = datetime_object.hour * 60 + datetime_object.minute
            if is_day:
                return "It is currently daytime. There are " + str(min_remaining) + " minutes until night."
            else:
                if min_remaining > 2:
                    return "It is night. There are " + str(min_remaining) + " minutes until day."
                return "It is night. Sunrise nears. Sentient retreats. Strike now, for in moments, the future decides itself!"
        else:
            return "Error grabbing API"

    @staticmethod
    def current_fissure(fissure_type):
        url = "https://api.warframestat.us/pc/" + "fissures"
        response = requests.get(url)
        if response.status_code == 200:
            parsed_json = json.loads(response.text)

            lith = 0
            meso = 0
            neo = 0
            axi = 0
            requiem = 0
            for fissure in parsed_json:
                if fissure['missionType'] == fissure_type:
                    if fissure['tierNum'] == 1:
                        lith += 1
                    elif fissure['tierNum'] == 2:
                        meso += 1
                    elif fissure['tierNum'] == 3:
                        neo += 1
                    elif fissure['tierNum'] == 4:
                        axi += 1
                    elif fissure['tierNum'] == 5:
                        requiem += 1

            total = lith + meso + neo + axi + requiem

            if total == 0:
                defection_egg = ""
                if fissure_type == "Defection":
                    defection_egg = "Really? You want to play Defection? ... "
                return defection_egg + "There are currently no " + fissure_type + " fissures active."

            type_count = 0
            if lith > 0:
                type_count += 1
            if meso > 0:
                type_count += 1
            if neo > 0:
                type_count += 1
            if axi > 0:
                type_count += 1
            if requiem > 0:
                type_count += 1

            plural1 = "are"
            plural2 = "fissures"
            if total == 1:
                plural1 = "is"
                plural2 = "fissure"
            compiled = "There " + plural1 + " " + str(total) + " " + fissure_type + " " + plural2 + " active. "
            processed_count = 0
            if lith > 0:
                compiled += str(lith) + " lith"
                processed_count += 1
                if processed_count == type_count:
                    compiled += "."

            if meso > 0:
                if processed_count > 0:
                    compiled += ", and "
                compiled += str(meso) + " meso"
                processed_count += 1
                if processed_count == type_count:
                    compiled += "."

            if neo > 0:
                if processed_count > 0:
                    compiled += ","
                    if processed_count + 1 == type_count:
                        compiled += " and "
                compiled += str(neo) + " neo"
                processed_count += 1
                if processed_count == type_count:
                    compiled += "."

            if axi > 0:
                if processed_count > 0:
                    compiled += ","
                    if processed_count + 1 == type_count:
                        compiled += " and "
                compiled += str(axi) + " axi"
                processed_count += 1
                if processed_count == type_count:
                    compiled += "."

            if requiem > 0:
                if processed_count > 0:
                    compiled += ","
                    if processed_count + 1 == type_count:
                        compiled += " and "
                compiled += str(requiem) + " requiem"
                processed_count += 1
                if processed_count == type_count:
                    compiled += "."

            return compiled

        else:
            return "Error grabbing API"


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Welcome, you can say Hello or Help. Which would you like to try?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CetusTimeIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("CetusTimeIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = WarframeAPIQuery.cetus_time()
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class CurrentArbitrationIntentHandler(AbstractRequestHandler):
    """Handler for Current Arbitration Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("CurrentArbitrationIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = WarframeAPIQuery.current_arbitration()
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class SurvivalCountIntentHandler(AbstractRequestHandler):
    """Handler for Survival Count Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("SurvivalCountIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = WarframeAPIQuery.current_fissure('Survival')
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class CaptureCountIntentHandler(AbstractRequestHandler):
    """Handler for Capture Count Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("CaptureCountIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = WarframeAPIQuery.current_fissure('Capture')
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class InterceptionCountIntentHandler(AbstractRequestHandler):
    """Handler for Interception Count Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("InterceptionCountIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = WarframeAPIQuery.current_fissure('Interception')
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class DefenseCountIntentHandler(AbstractRequestHandler):
    """Handler for Defense Count Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("DefenseCountIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = WarframeAPIQuery.current_fissure('Defense')
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class MobileDefenseCountIntentHandler(AbstractRequestHandler):
    """Handler for Mobile Defense Count Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("MobileDefenseCountIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = WarframeAPIQuery.current_fissure('Mobile Defense')
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class SabotageCountIntentHandler(AbstractRequestHandler):
    """Handler for Sabotage Count Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("SabotageCountIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = WarframeAPIQuery.current_fissure('Sabotage')
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class RescueCountIntentHandler(AbstractRequestHandler):
    """Handler for Rescue Count Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("RescueCountIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = WarframeAPIQuery.current_fissure('Rescue')
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class DisruptionCountIntentHandler(AbstractRequestHandler):
    """Handler for Disruption Count Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("DisruptionCountIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = WarframeAPIQuery.current_fissure('Disruption')
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class ExterminateCountIntentHandler(AbstractRequestHandler):
    """Handler for Exterminate Count Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("ExterminateCountIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = WarframeAPIQuery.current_fissure('Extermination')
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class DefectionCountIntentHandler(AbstractRequestHandler):
    """Handler for Defection Count Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("DefectionCountIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = WarframeAPIQuery.current_fissure('Defection')
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class SpyCountIntentHandler(AbstractRequestHandler):
    """Handler for Spy Count Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("SpyCountIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = WarframeAPIQuery.current_fissure('Spy')
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class HiveCountIntentHandler(AbstractRequestHandler):
    """Handler for Hive Count Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("HiveCountIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = WarframeAPIQuery.current_fissure('Hive')
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class VorIntentHandler(AbstractRequestHandler):
    """Handler for Vor Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("VorIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Look at them, they come to this place when they know they are not pure. Tenno use the keys, " \
                       "but they are mere trespassers. Only I, Vor, know the true power of the Void. I was cut in " \
                       "half, destroyed, but through it's Janus Key, the Void called to me. It brought me here and" \
                       " here I was reborn. We cannot blame these creatures, they are being led by a false prophet," \
                       " an impostor who knows not the secrets of the Void. Behold the Tenno, come to scavenge and " \
                       "desecrate this sacred realm. My brothers, did I not tell of this day? Did I not prophesize " \
                       "this moment? Now, I will stop them. Now I am changed, reborn through the energy of the Janus" \
                       " Key. Forever bound to the Void. Let it be known, if the Tenno want true salvation, they" \
                       " will lay down their arms, and wait for the baptism of my Janus key. It is time. I will " \
                       "teach these trespassers the redemptive power of my Janus key. They will learn it's simple" \
                       " truth. The Tenno are lost, and they will resist. But I, Vor, will cleanse this place of" \
                       " their impurity."
        speak_output = speak_output.replace("Janus", "<phoneme alphabet=\"ipa\" ph=\"jɑnəs\">Janus</phoneme>")
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )



class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "You can say hello to me! How can I help?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Goodbye!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(CetusTimeIntentHandler())
sb.add_request_handler(CurrentArbitrationIntentHandler())
sb.add_request_handler(SurvivalCountIntentHandler())
sb.add_request_handler(CaptureCountIntentHandler())
sb.add_request_handler(InterceptionCountIntentHandler())
sb.add_request_handler(DefenseCountIntentHandler())
sb.add_request_handler(MobileDefenseCountIntentHandler())
sb.add_request_handler(SabotageCountIntentHandler())
sb.add_request_handler(RescueCountIntentHandler())
sb.add_request_handler(DisruptionCountIntentHandler())
sb.add_request_handler(ExterminateCountIntentHandler())
sb.add_request_handler(DefectionCountIntentHandler())
sb.add_request_handler(SpyCountIntentHandler())
sb.add_request_handler(HiveCountIntentHandler())

sb.add_request_handler(VorIntentHandler())

sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()