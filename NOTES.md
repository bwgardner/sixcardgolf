# NOTES

Handle default sort order of values? Should I treat 2 through 10 as numeric?
Suit Color?
Shortnames?

I feel like Hand should inherit from Deck, which should inherit from Card.

Is Deck.order as a range object OK? It seems to me it should be an explicit list.

Add an "add" method to Deck so you can put cards back into it (one at a time or in bulk like adding a second Deck or the Discard Pile = a Deck)

A Hand is really just a Deck that starts empty until you deal, and may have a Hand Limit (max size), and belongs to a Player


