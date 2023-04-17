# Harvard CS50 AI (Week 3) Project 7 : Crossword

This is the seventh project of [Harvard CS50's Introduction to Artificial Intelligence course](https://cs50.harvard.edu/ai/2020/), the only project of Week 3.

## My Outputs

![Screenshot of my output on terminal](https://cdn.discordapp.com/attachments/1091358303063396496/1097353198668361768/output.png)

## Objective

Write an AI to generate crossword puzzles.

## Background

How might you go about generating a crossword puzzle? Given the structure of a crossword puzzle (i.e., which squares of the grid are meant to be filled in with a letter), and a list of words to use, the problem becomes one of choosing which words should go in each vertical or horizontal sequence of squares. We can model this sort of problem as a constraint satisfaction problem. Each sequence of squares is one variable, for which we need to decide on its value (which word in the domain of possible words will fill in that sequence).

The challenge ahead, then, is write a program to find a satisfying assignment: a different word (from a given vocabulary list) for each variable such that all of the unary and binary constraints are met.
