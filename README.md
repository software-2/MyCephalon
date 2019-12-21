# My Cephalon - Warframe Companion
My Cephalon is an Alexa skill for Warframe. The goal is to answer the question "should I log in and play right now?"

Why this one when there's a few others out there already?

* Console support! Every other skill works only for PC.
* Other skills are outdated - Many new game modes are not included
* Better algorithms - You don't want to know what the details of 12 invasions are, you want to know any of them have a reward worth doing.
* Look at them, they come to this place...

## Install

The skill can be added to your Alexa account by searching for the "My Cephalon" skill (or search for "Warframe" - It's the skill with Nef twirling his mustache.)

Alternatively, here's a [direct link](https://alexa.amazon.com/spa/index.html#skills/dp/B082YYQ2V2/?ref=skill_dsk_skb_sr_3&qid=1576960689).

### Console Support

By default, queries are done on the PC platform. To change to PS4/Xbox/Switch say "Change platforms".

## Questions

There are two types of questions - Direct information queries like these:

* Is the Sentient ship here?
* What is the current Arbitration?
* How long until night in Cetus?
* Is the Void Trader here?
* What is the weather in the Orb Vallis?

And summary questions:

* Are there any Invasions worth doing?
* How many Survival/Capture/etc fissures are there?

Easter Eggs:
* Look at them
* Give unto the Void
* How many Defection fissures are there?

## Known Issues

* The official Sentient Ship API info is awful. It clearly is going to change, and when it does, this skill will break. Nothing I can do about it right now, unfortunately.

* My Cephalon is a dumb name - I originally was going to use "The Void" and have all sorts of Nef-themed stuff. But Amazon won't let you have a skill with "the" in the name.

* Alexa doesn't always process the word "Cephalon". If she says "Sorry, I'm not sure", that means the algorithm has failed you. Try again, or say "Open My Cephalon" first - that seems to have better luck in my experience.

* The time until Baro arrives doesn't happen. Oddly enough, every time I sit down to work on this skill, Baro is here, so I can't test the opposite.

## Contribute

Contributions are welcome! Please feel free to reach out to me or submit a pull request.

If you have problems, please file a bug. 

## Special Thanks

A heartfelt thanks to the Warframe Community Developers! [Their API](https://docs.warframestat.us/) is vastly superior to the official one. Thanks to Tobiah for putting up with my documentation questions!