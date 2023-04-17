import sys
import copy

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for var in self.crossword.variables:
            for term in self.crossword.words:
                if len(term) != var.length:
                    self.domains[var].remove(term)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        revision = False
        overlap = self.crossword.overlaps[x, y]
        if overlap:
            m, n = overlap
            removable = set()
            for domain_of_x in self.domains[x]:
                possible_overlap = False
                for domain_of_y in self.domains[y]:
                    if domain_of_x != domain_of_y and domain_of_x[m] == domain_of_y[n]:
                        possible_overlap = True
                        break

                if not possible_overlap:
                    removable.add(domain_of_x)
            if removable:
                self.domains[x] -= removable
                revision = True

        return revision

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        if not arcs:
            serie = []
            for v1 in self.crossword.variables:
                for v2 in self.crossword.neighbors(v1):
                    serie.append((v1, v2))
        else:
            serie = list(arcs)
        while serie:
            a, b = serie.pop(0)
            bset = set()
            bset.add(b)
            if self.revise(a, b):
                if len(self.domains[a]) == 0:
                    return False
                for k in self.crossword.neighbors(a) - bset:
                    serie.append((k, a))

        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for i in self.crossword.variables:
            if i not in assignment.keys():
                return False
            if assignment[i] not in self.crossword.words:
                return False

        return True

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        for i in assignment:
            term1 = assignment[i]
            if i.length != len(term1):
                return False

            for j in assignment:
                term2 = assignment[j]
                if i != j:
                    if term1 == term2:
                        return False

                    overlap = self.crossword.overlaps[i, j]
                    if overlap:
                        m, n = overlap
                        if term1[m] != term2[n]:
                            return False

        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        companions = self.crossword.neighbors(var)
        for i in assignment:
            if i in companions:
                companions.remove(i)

        final = []

        for j in self.domains[var]:
            removed = 0
            for k in companions:
                for l in self.domains[k]:
                    overlap = self.crossword.overlaps[var, k]
                    if overlap:
                        m, n = overlap
                        if j[m] != l[n]:
                            removed += 1

            final.append([j, removed])

        final.sort(key=lambda x: (x[1]))
        return [p[0] for p in final]

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        varlist = []
        for term in self.crossword.variables:
            if term not in assignment:
                varlist.append([term, len(self.domains[term]), len(self.crossword.neighbors(term))])

        if varlist:
            varlist.sort(key=lambda x: (x[1], -x[2]))
            return varlist[0][0]
        return None

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        if self.assignment_complete(assignment):
            return assignment
        term = self.select_unassigned_variable(assignment)
        for value in self.order_domain_values(term, assignment):
            assgn2 = assignment.copy()
            assgn2[term] = value
            if self.consistent(assgn2):
                final = self.backtrack(assgn2)
                if final:
                    return final

        return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()