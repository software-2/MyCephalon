# -*- coding: utf-8 -*-

import os
import requests
import json
import math
import logging
from datetime import datetime

import ask_sdk_core.utils as ask_utils
from ask_sdk_core.utils import is_intent_name
from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response
from ask_sdk_model.ui import SimpleCard
from ask_sdk_s3.adapter import S3Adapter


class WarframeAPIQuery:

    @staticmethod
    def parse_hms(hms_string):
        constructed_time = ""
        if hms_string.find('h') == -1:
            constructed_time = "0h " + hms_string

        if hms_string.find('s') == -1:
            constructed_time = constructed_time + "0s"

        if hms_string.find('m') == -1:
            datetime_object = datetime.strptime(constructed_time, '%Hh %Ss')
        else:
            datetime_object = datetime.strptime(constructed_time, '%Hh %Mm %Ss')

        return datetime_object.hour * 60 + datetime_object.minute

    @staticmethod
    def generate_english_time(diff):
        # The general concept here is to avoid "Spock Over-Accuracy"
        if diff.days > 0:
            sub_hours = (diff.seconds - 86400) / 60 / 60
            plural_day = "days"
            if diff.days == 1:
                plural_day = "day"
            plural_hour = "hours"
            if sub_hours == 1:
                plural_hour = "hour"
            return str(diff.days) + " " + plural_day + " and " + str(sub_hours) + plural_hour
        else:
            hours = math.floor(diff.seconds / 60 / 60)
            plural_hour = "hours"
            if hours == 1:
                plural_hour = "hour"
            minutes = math.floor((diff.seconds / 60) - (hours * 60))
            plural_minute = "minutes"
            if minutes == 1:
                plural_minute = "minute"
            if hours > 0:
                hours_string = str(hours) + " " + plural_hour + " and "
            else:
                hours_string = ""
            return hours_string + str(minutes) + " " + plural_minute

    @staticmethod
    def current_arbitration(platform):
        url = "https://api.warframestat.us/" + platform + "/" + "arbitration"
        response = requests.get(url)
        if response.status_code == 200:
            parsed_json = json.loads(response.text)
            expiry = parsed_json['expiry']
            datetime_object = datetime.strptime(expiry, '%Y-%m-%dT%H:%M:%S.000Z')
            diff = datetime.now() - datetime_object

            # I got one response that was:
            # {"activation":"2019-11-30T16:05:00.000Z","expiry":"2019-11-30T17:05:00.000Z","solnode":"SolNode308",
            # "node":"undefined (undefined)","type":"Disruption"}
            # So handling that bug as gracefully as I can

            if 'enemy' in parsed_json:
                enemy = parsed_json['enemy']
            else:
                enemy = ""

            mode_type = parsed_json['type']

            if enemy == "Grineer":
                enemy = "<sub alias=\"grah near\">Grineer</sub>"

            if diff.total_seconds() > 0:
                return "I'm not sure what the current Arbitration is - The API hasn't updated to the new one yet. " \
                       "But, the old one was " + enemy + " " + mode_type + "."

            return "The current Arbitration is " + enemy + " " + mode_type + "."
        else:
            return "Error grabbing API"

    @staticmethod
    def cetus_time(platform):
        url = "https://api.warframestat.us/" + platform + "/" + "cetusCycle"
        response = requests.get(url)
        if response.status_code == 200:
            parsed_json = json.loads(response.text)
            is_day = parsed_json['isDay']
            time_remaining = parsed_json['timeLeft']
            min_remaining = WarframeAPIQuery.parse_hms(time_remaining)
            if is_day:
                return "It is currently daytime. There are " + str(min_remaining) + " minutes until night."
            else:
                if min_remaining > 2:
                    return "It is night. There are " + str(min_remaining) + " minutes until day."
                return "It is night. Sunrise nears. Sentient retreats. " \
                       "Strike now, for in moments, the future decides itself!"
        else:
            return "Error grabbing API"

    @staticmethod
    def fortuna_time(platform):
        url = "https://api.warframestat.us/" + platform + "/" + "vallisCycle"
        response = requests.get(url)
        if response.status_code == 200:
            parsed_json = json.loads(response.text)
            is_warm = parsed_json['isWarm']
            time_remaining = parsed_json['timeLeft']
            min_remaining = WarframeAPIQuery.parse_hms(time_remaining)

            plural1 = "are"
            plural2 = "minutes"
            if min_remaining == 1:
                plural1 = "is"
                plural2 = "minute"
            if is_warm:
                return "It is currently warm. There " + plural1 + " " + str(min_remaining) + " " + plural2 +\
                       " until it's cold."
            else:
                return "It is currently cold. There are " + str(min_remaining) + " minutes until it's warm."
        else:
            return "Error grabbing API"

    @staticmethod
    def void_trader_time(platform):
        url = "https://api.warframestat.us/" + platform + "/" + "voidTrader"
        response = requests.get(url)
        if response.status_code == 200:
            parsed_json = json.loads(response.text)
            is_active = parsed_json['active']
            start_time = parsed_json['activation']
            end_time = parsed_json['expiry']
            location = parsed_json['location']

            baro = "<phoneme alphabet=\"ipa\" ph=\"bero\">Baro</phoneme>"

            if is_active:
                relay = location[0:location.find("(")-1]
                planet = location[location.find("(")+1:location.find(")")]

                datetime_object = datetime.strptime(end_time, '%Y-%m-%dT%H:%M:%S.000Z')
                diff = datetime_object - datetime.now()
                remaining = WarframeAPIQuery.generate_english_time(diff)

                return baro + " is here! He's at the " + relay + " on " + planet + ". He'll be here for " \
                                                                                   "another " + remaining + "."
            else:
                return baro + " is not here right now."

        else:
            return "Error grabbing API"

    @staticmethod
    def current_fissure(platform, fissure_type):
        url = "https://api.warframestat.us/" + platform + "/" + "fissures"
        response = requests.get(url)
        if response.status_code == 200:
            parsed_json = json.loads(response.text)

            lith = 0
            meso = 0
            neo = 0
            axi = 0
            requiem = 0
            for fissure in parsed_json:
                if fissure_type in fissure['missionType']:
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

    @staticmethod
    def invasions_worth_it(platform):
        url = "https://api.warframestat.us/" + platform + "/" + "invasions"
        response = requests.get(url)
        if response.status_code == 200:
            parsed_json = json.loads(response.text)

            for invasion in parsed_json:
                reward_types = invasion['rewardTypes']
                percent = int(invasion['completion'])
                for reward in reward_types:
                    if reward == "reactor":
                        return "Yes! There's a golden potato invasion! It's currently " + str(percent) + "% complete."
                    if reward == "catalyst":
                        return "Yes! There's a blue potato invasion! It's currently " + str(percent) + "% complete."
                    if reward == "forma":
                        return "Maybe? There's a forma invasion. It's currently " + str(percent) + \
                               "% complete. But why not just go run a single fissure?"
            return "Nope, I wouldn't bother."
        else:
            return "Error grabbing API"


def get_platform(handler_input):
    attr = handler_input.attributes_manager.persistent_attributes

    if "Platform" in attr:
        platform = attr["Platform"]
        if platform == "PC":
            return "pc"
        if platform == "Xbox":
            return "xb1"
        if platform == "PlayStation":
            return "ps4"
        if platform == "switch":
            return "swi"
        return "pc"
    else:
        # This hasn't been set yet. Default to PC.
        return "pc"


def increment_usage_count(handler_input):
    persistent_attr = handler_input.attributes_manager.persistent_attributes

    usage_count = 1
    if "UsageCount" in persistent_attr:
        usage_count += int(persistent_attr["UsageCount"])

    persistent_attr["UsageCount"] = usage_count
    handler_input.attributes_manager.save_persistent_attributes()


class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Welcome to The Void. If you need help, just say \"help\", otherwise what can I do for you?"

        return (
            handler_input.response_builder
                         .speak(speak_output)
                         .ask(speak_output)
                         .response
        )


class CetusTimeIntentHandler(AbstractRequestHandler):
    """Handler for Cetus Time Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("CetusTimeIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        increment_usage_count(handler_input)
        platform = get_platform(handler_input)
        speak_output = WarframeAPIQuery.cetus_time(platform)
        return (
            handler_input.response_builder
                         .speak(speak_output)
                         .response
        )


class FortunaTimeIntentHandler(AbstractRequestHandler):
    """Handler for Fortuna Time Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("FortunaTimeIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        increment_usage_count(handler_input)
        platform = get_platform(handler_input)
        speak_output = WarframeAPIQuery.fortuna_time(platform)
        return (
            handler_input.response_builder
                         .speak(speak_output)
                         .response
        )


class VoidTraderTimeIntentHandler(AbstractRequestHandler):
    """Handler for Void Trader Time Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("VoidTraderTimeIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        increment_usage_count(handler_input)
        platform = get_platform(handler_input)
        speak_output = WarframeAPIQuery.void_trader_time(platform)
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
        increment_usage_count(handler_input)
        platform = get_platform(handler_input)
        speak_output = WarframeAPIQuery.current_arbitration(platform)
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
        increment_usage_count(handler_input)
        platform = get_platform(handler_input)
        speak_output = WarframeAPIQuery.current_fissure(platform, 'Survival')
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
        increment_usage_count(handler_input)
        platform = get_platform(handler_input)
        speak_output = WarframeAPIQuery.current_fissure(platform, 'Capture')
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
        increment_usage_count(handler_input)
        platform = get_platform(handler_input)
        speak_output = WarframeAPIQuery.current_fissure(platform, 'Interception')
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
        increment_usage_count(handler_input)
        platform = get_platform(handler_input)
        speak_output = WarframeAPIQuery.current_fissure(platform, 'Defense')
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
        increment_usage_count(handler_input)
        platform = get_platform(handler_input)
        speak_output = WarframeAPIQuery.current_fissure(platform, 'Mobile Defense')
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
        increment_usage_count(handler_input)
        platform = get_platform(handler_input)
        speak_output = WarframeAPIQuery.current_fissure(platform, 'Sabotage')
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
        increment_usage_count(handler_input)
        platform = get_platform(handler_input)
        speak_output = WarframeAPIQuery.current_fissure(platform, 'Rescue')
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
        increment_usage_count(handler_input)
        platform = get_platform(handler_input)
        speak_output = WarframeAPIQuery.current_fissure(platform, 'Disruption')
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
        increment_usage_count(handler_input)
        platform = get_platform(handler_input)
        speak_output = WarframeAPIQuery.current_fissure(platform, 'Extermination')
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
        platform = get_platform(handler_input)
        speak_output = WarframeAPIQuery.current_fissure(platform, 'Defection')
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
        increment_usage_count(handler_input)
        platform = get_platform(handler_input)
        speak_output = WarframeAPIQuery.current_fissure(platform, 'Spy')
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
        increment_usage_count(handler_input)
        platform = get_platform(handler_input)
        speak_output = WarframeAPIQuery.current_fissure(platform, 'Hive')
        return (
            handler_input.response_builder
                         .speak(speak_output)
                         .response
        )


class ExcavationCountIntentHandler(AbstractRequestHandler):
    """Handler for Excavation Count Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("ExcavationCountIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        increment_usage_count(handler_input)
        platform = get_platform(handler_input)
        speak_output = WarframeAPIQuery.current_fissure(platform, 'Excavation')
        return (
            handler_input.response_builder
                         .speak(speak_output)
                         .response
        )


class InvasionsWorthItIntentHandler(AbstractRequestHandler):
    """Handler for Invasions Worth It Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("InvasionsWorthItIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        increment_usage_count(handler_input)
        platform = get_platform(handler_input)
        speak_output = WarframeAPIQuery.invasions_worth_it(platform)
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
        increment_usage_count(handler_input)
        vor_pasta = "Look at them, they come to this place when they know they are not pure. Tenno use the keys, " \
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
        speak_output = vor_pasta.replace("Janus", "<phoneme alphabet=\"ipa\" ph=\"jɑnəs\">Janus</phoneme>")

        if hasattr(handler_input.request_envelope.context.system.device.supported_interfaces, 'display'):
            return (handler_input.response_builder
                    .set_card(SimpleCard("Vor", vor_pasta))
                    .speak(speak_output)
                    .response
                    )

        return (
            handler_input.response_builder
                         .speak(speak_output)
                         .response
        )


class GiveUntoTheVoidIntentHandler(AbstractRequestHandler):
    """Handler for Give Unto The Void Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("GiveUntoTheVoidIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        increment_usage_count(handler_input)
        speak_output = "Scoundrels, heretics, believers! Listen! Do you crave redemption? Do you feel that " \
                       "burden of poverty crushing you? You need relief. But how, How can you ask for help " \
                       "unless you first help yourself! Give. Unto the Void. I was once a wretched crewman," \
                       " breaking my back just to earn a credit. Then, I found that glorious energy. Oh, and" \
                       " when I gave my first offering, how its richness rained down upon me! Do you want what" \
                       " I have received? Do you want it for yourself? Then give. Unto the Void. Let your credits" \
                       " be the seeds of your prosperity. Give unto the Void! And you will be rewarded a " \
                       "hundredfold! The Void be the word, and the word be profit."

        if hasattr(handler_input.request_envelope.context.system.device.supported_interfaces, 'display'):
            return (handler_input.response_builder
                    .set_card(SimpleCard("Nef Anyo", speak_output))
                    .speak(speak_output)
                    .response
                    )

        return (
            handler_input.response_builder
                         .speak(speak_output)
                         .response
        )


class ChangePlatformsIntentHandler(AbstractRequestHandler):
    """Handler for Change Platforms Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("ChangePlatformsIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        slots = handler_input.request_envelope.request.intent.slots

        if "Platform" in slots:
            platform = slots["Platform"].value

            handler_input.attributes_manager.persistent_attributes["Platform"] = platform
            handler_input.attributes_manager.save_persistent_attributes()

            speak_output = "Okay, your platform is set to " + platform + \
                           ". I'll give you info about that platform from now on."

            return (
                handler_input.response_builder
                             .speak(speak_output)
                             .response
            )
        else:
            # This means the "don't worry about it, we'll handle it for you" dialog failed to handle it
            speak_output = "Something's gone wrong. Please ask again."
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
        speak_output = "You can ask me about many things in Warframe. For example: What is the current Arbitration? " \
                       "What is the weather in the Orb Vallis? How long until it's night in Cetus? How long until " \
                       "<phoneme alphabet=\"ipa\" ph=\"bero\">Baro</phoneme> arrives? If you want to know about a " \
                       "specific fissure type, ask something like: How many survivals are there? If you want to " \
                       "check if there's a rare Invasion going on, ask: Are there any Invasions worth doing? By " \
                       "default, I'll give you information on the PC version of the game. If you want to switch to" \
                       " a console just say \"Change platforms\". So, what would you like?"

        help_samples = "What is the current Arbitration?\nWhat is the weather in the Orb Vallis?\nHow long until " \
                       "it's night in Cetus?\nHow long until Baro arrives?\nHow many survivals are there?\nAre " \
                       "there any Invasions worth doing?"

        if hasattr(handler_input.request_envelope.context.system.device.supported_interfaces, 'display'):
            return (handler_input.response_builder
                    .set_card(SimpleCard("Example Questions", help_samples))
                    .speak(speak_output)
                    .response
                    )

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


s3_adapter = S3Adapter(bucket_name=os.environ["S3_PERSISTENCE_BUCKET"])
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.
sb = CustomSkillBuilder(persistence_adapter=s3_adapter)

sb.add_request_handler(ChangePlatformsIntentHandler())

sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(CetusTimeIntentHandler())
sb.add_request_handler(FortunaTimeIntentHandler())
sb.add_request_handler(VoidTraderTimeIntentHandler())
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
sb.add_request_handler(ExcavationCountIntentHandler())

sb.add_request_handler(InvasionsWorthItIntentHandler())

sb.add_request_handler(VorIntentHandler())
sb.add_request_handler(GiveUntoTheVoidIntentHandler())

sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
# make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers
sb.add_request_handler(IntentReflectorHandler())

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()
