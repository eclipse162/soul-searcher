# Soul Searcher
This project draws inspiration from [spelltable.com](http://spelltable.com), but instead of detecting Magic: The Gathering cards, it will instead use Weiss Schwarz cards and display relevant information on the screen.

There is an active to-do list that shows the process and ongoing tasks to be finished, and references used will be updated frequently.

## First Steps: Search cards using websites
Features that are currently in progress or will be implemented in the future include:
* Search English edition cards by ID or with queries using the [Weiss Schwarz EN website](https://en.ws-tcg.com)
* Search Japanese edition cards by card stats (power, level, cost, etc.) using the [Heart of the Cards website](https://www.heartofthecards.com/code/wscardsearch.html)
* Implementing search features to be able to used by a Discord bot

## Second Step: Training a Card Identifier
Using a custom Haar Classifier, the program will automatically detect Weiss Schwarz cards and use the above search functions to display useful information about the card.

## Last Step: Design an Interface
After testing the card identifier, the interface used by the program will either be hosted on a website or displayed by an external GUI. There are no concrete plans at the moment.

Any suggestions are welcomed. Stay tuned for more updates!
