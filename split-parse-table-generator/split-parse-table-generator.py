from tabulate import tabulate

# script to determine first- and follow-sets of a given grammar
# therefore it also decides if a grammar is LL(1)


class ParseTableGen(object):
    # every production has to stand on its own. Seperators from the likes "|" are not allowed.
    # Examples: 'S = A B c', 'S = ', 'A = id number c'
    # epsilon productions resembled by empty right side e.g.: 'S = '
    productions = []
    eps_productions = ()
    terminals = []
    non_terminals = []

    # specific to Calc-context-free languages that have a collision between bytes and string-ending symbols (like comma)
    byte_symbol = ""
    end_of_string_symbol = ""

    # first and follow set dicts
    first_sets = {}
    follow_sets = {}
    parse_table = []

    # initializes a ParseTableGen object given a grammar and calculates first/follow sets and the parse table
    # The 'byte_symbol' can be added as a parameter if one wants to process calc-context-free grammars and therefore
    # needs to specify a non-terminal that represents bytes and can cause collisions with the end of string symbol
    def __init__(self, productions, byte_symbol=None, end_of_string_symbol=None):
        self.format_productions(productions)
        self.format_init_sets()
        self.first_sets, self.follow_sets = self.first_and_follow()
        self.parse_table = self.create_table()
        if byte_symbol is not None:
            if byte_symbol not in self.terminals:
                print("ERROR! Symbol for bytes 'byte_symbol' has to be a terminal symbol!"
                      " Symbol entered: " + str(byte_symbol))
            else:
                self.byte_symbol = byte_symbol
            if end_of_string_symbol is not None:
                if end_of_string_symbol not in self.terminals:
                    print("ERROR! Symbol for end of string 'end_of_string_symbol' has to be a terminal symbol!"
                          " Symbol entered: " + str(end_of_string_symbol))
                else:
                    self.end_of_string_symbol = end_of_string_symbol
                    self.split_table()

    # basic formatting to bring productions into correct format
    def format_productions(self, productions):
        self.productions = tuple(tuple(prod.replace(' ', '').split('=')) for prod in productions)
        for prod in productions:
            pr = prod.replace(' ', ''). split('=')
            non_t = str(pr.pop(0))
            if len(pr[0]) == 0:
                non_t_tuple = (non_t, 'epsilon')
                self.eps_productions = (non_t_tuple,) + self.eps_productions

    # initialize non-terminals and terminals
    def format_init_sets(self):
        self.non_terminals = set(nt for nt, x in self.productions)
        self.terminals = set(symbol for y, expression in self.productions for symbol in expression
                             if not (symbol.isalpha() and symbol.isupper()))

    # calculates first and follow sets
    def first_and_follow(self):
        # first & follow sets, epsilon-productions
        first = {i: set() for i in self.non_terminals}
        # initialize trivial first sets for terminals:
        first.update((i, {i}) for i in self.terminals)
        follow = {i: set() for i in self.non_terminals}
        epsilon = set()

        while True:
            updated = False

            for nt, expression in self.productions:
                # FIRST set w.r.t epsilon-productions
                for symbol in expression:
                    updated |= self.union(first[nt], first[symbol])
                    if symbol not in epsilon:
                        break
                else:
                    updated |= self.union(epsilon, {nt})

                # FOLLOW set w.r.t epsilon-productions
                aux = follow[nt]
                for symbol in reversed(expression):
                    if symbol in follow:
                        updated |= self.union(follow[symbol], aux)
                    if symbol in epsilon:
                        aux = aux.union(first[symbol])
                    else:
                        aux = first[symbol]

            if not updated:
                for non_t in epsilon:
                    first[non_t].add('epsilon')
                # print("First Sets:\n " + str(first))
                # print("Follow Sets:\n " + str(follow))
                return first, follow

    # initializes empty parse table structure with terminals and non-terminals as row and column headers respectively
    def init_table(self):
        w, h = len(self.terminals)+1, len(self.non_terminals)+1
        table = [[" " for x in range(w)] for y in range(h)]
        i = 1
        for non_t in self.non_terminals:
            table[i][0] = non_t
            i += 1
        i = 1
        for t in self.terminals:
            table[0][i] = t
            i += 1
        # print("Initialized table:\n" + str(tabulate(table, tablefmt="fancy_grid")))
        return table

    # simple helper function to retrieve the index of a symbol s from the parse table
    def get_table_position(self, parse_table, s):
        if s in self.non_terminals:
            for i in range(len(self.non_terminals)+1):
                if parse_table[i][0] == s:
                    return i
        elif s in self.terminals:
            for i in range(len(self.terminals)+1):
                if parse_table[0][i] == s:
                    return i
        elif s == "$":
            return len(self.terminals)+1
        else:
            print("ERROR! in \"get_table_position(" + str(s) + ")\". Not a valid terminal or non-terminal symbol. ")

    def return_first_set(self, symbols):
        if symbols == 'epsilon':
            return 'epsilon'
        elif len(symbols) == 1:
            return self.first_sets[symbols[0]]
        elif len(symbols) == 0:
            return []
        elif len(symbols) > 1:
            symbols = list(symbols)
            Y_1 = symbols[0]
            symbols.pop(0)
            if 'epsilon' not in self.first_sets[Y_1]:
                return self.first_sets[Y_1]
            else:
                new_set = []
                new_set += self.first_sets[Y_1]
                new_set.remove('epsilon')
                new_set += self.return_first_set(symbols)
                eps_flag = True
                for Y in symbols:
                    if 'epsilon' not in self.first_sets[Y]:
                        eps_flag = False
                if eps_flag:
                    new_set += 'epsilon'
                return new_set

    # creates the parse table out of first and follow sets
    def create_table(self):
        CRED = '\033[91m'
        CEND = '\033[0m'
        parse_table = self.init_table()
        all_productions = self.productions + self.eps_productions
        for prod in all_productions:
            non_t = prod[0]
            r_side = ""
            i = 1
            while i < len(prod):
                r_side += prod[i]
                i += 1
            eps_in_set = False
            if r_side == 'epsilon':
                eps_in_set = True
            r_side_f_set = self.return_first_set(r_side)
            for t in self.terminals:
                if not eps_in_set:
                    if t in r_side_f_set:
                        pos_n = self.get_table_position(parse_table, non_t)
                        pos_t = self.get_table_position(parse_table, t)
                        prod_formatted = str(prod[0]) + " -> " + str(prod[1])
                        current_entry = parse_table[pos_n][pos_t]
                        if current_entry is " ":
                            parse_table[pos_n][pos_t] = prod_formatted
                        else:
                            print("ERROR! Collision at parse table with Non-terminal: " + str(non_t) +
                                  " and terminal: " + str(t))
                            parse_table[pos_n][pos_t] = CRED + current_entry + CEND + "\n" \
                                                        + CRED + prod_formatted + CEND
                if eps_in_set:
                    if t in self.follow_sets[non_t]:
                        pos_n_2 = self.get_table_position(parse_table, non_t)
                        pos_t_2 = self.get_table_position(parse_table, t)
                        prod_formatted = str(prod[0]) + " -> " + str(prod[1])
                        current_entry = parse_table[pos_n_2][pos_t_2]
                        if current_entry is " ":
                            parse_table[pos_n_2][pos_t_2] = prod_formatted
                        else:
                            print("ERROR! Collision at parse table with Non-terminal: " + str(non_t) +
                                  " and terminal: " + str(t))
                            parse_table[pos_n_2][pos_t_2] = CRED + current_entry + CEND + "\n"\
                                                            + CRED + prod_formatted + CEND
        print("\nParse table: ")
        print(tabulate(parse_table, tablefmt="fancy_grid"))
        return parse_table

    #
    def split_table(self):
        parse_table = self.parse_table.copy()
        byte_pos = self.get_table_position(parse_table, self.byte_symbol)
        end_symbol_pos = self.get_table_position(parse_table, self.end_of_string_symbol)
        non_t = ""
        for row in parse_table:
            if not row[byte_pos] == " " and len(row[byte_pos]) > 1:
                non_t = row[byte_pos][0]
        non_t_pos = self.get_table_position(parse_table, non_t)
        # byte_rule = parse_table[non_t_pos][byte_pos]
        end_symbol_rule = parse_table[non_t_pos][end_symbol_pos]
        parse_table.insert(non_t_pos+1, [" " for _ in range(len(self.terminals) + 1)])
        parse_table[non_t_pos+1][0] = non_t + " (acc == 0)"
        parse_table[non_t_pos][0] = non_t + " (acc > 0)"
        parse_table[non_t_pos][end_symbol_pos] = " "
        parse_table[non_t_pos+1][end_symbol_pos] = end_symbol_rule

        print("\nCalc-context-free Parse Table: ")
        print(tabulate(parse_table, tablefmt="fancy_grid"))

    @staticmethod
    # perform union between two sets with '|' operator
    def union(first, begins):
        n = len(first)
        first |= begins
        return len(first) != n


if __name__ == '__main__':
    # ---- Test Grammar 1 ---- #
    productions_1 = ["S = T E", "E = + T E", "E = ", "T = F K", "K = * F K", "K = ", "F = ( S )", "F = n"]
    # ParseTableGen(productions_1)

    # ---- Test Grammar 2 ---- #
    productions_2 = ["S = F", " S = ( S + F )", "F = a"]
    # ParseTableGen(productions_2)

    # ---- Test Grammar 3 ---- #
    productions_3 = ["S = A a", "A = B D", "B = b", "B = ", "D = d", "D = "]
    # ParseTableGen(productions_3)

    # ---- Test Grammar 4 ---- #
    productions_4 = ["S = T e", "T = R", "T = a T c", "R = ", "R = b R"]
    # ParseTableGen(productions_4)

    # ---- Test Grammar 5 (netstring grammar) ---- #
    # b = byte
    productions_5 = ["S = 0 D : R ,", "S = 1 D : T ,", "R = S R", "R = ", "T = b T", "T = ",
                     "D = 1 N", "D = ", "N = 0 N", "N = "]
    ParseTableGen(productions_5, "b", ",")
    # TODO: splitting the parse table as to avoid collision with "bytes" in calc-context free languages / netstrings
