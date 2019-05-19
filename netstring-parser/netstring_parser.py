# https://github.com/eliben/code-for-blog/blob/master/2009/py_rd_parser_example/rd_parser_bnf.py

import lexer


class ParseError(Exception):
    pass


class CalcParser(object):
    # once the outermost container size (outer_size) is read, set this flag to False
    outer_flag = True
    leading_zero = False
    empty_netstring = False
    container_stack = []
    # Size of the outermost container (on which position does the container end)
    outer_size = 1
    # Current position of the symbol in the outermost netstring container
    cur_pos = 0

    def __init__(self):
        lex_rules = [
            ('0',                    '0'),
            ('[1-9]',           'NDIGIT'),
            ('[0-9]',           'ZDIGIT'),
            ('\:',                   ':'),
            ('\,',                   ','),
            ('.',                 'BYTE'),
        ]

        self.lexer = lexer.Lexer(lex_rules, skip_whitespace=True)
        self._clear()

    def parse(self, line):
        """ Parse a new line of input and return its result.
            Variables defined in previous calls to parse can be
            used in following ones.
            ParseError can be raised in case of errors.
        """
        self.lexer.input(line)
        self._get_next_token()
        return self._netstring()

    def _clear(self):
        self.cur_token = None
        self.var_table = {}

    def _error(self, msg):
        raise ParseError(msg)

    def _get_next_token(self):
        try:
            self.cur_token = self.lexer.token()

            if self.cur_token is None:
                self.cur_token = lexer.Token(None, None, None)
        except lexer.LexerError as e:
            self._error('Lexer error at position %d' % e.pos)

    def _match(self, type):
        """ The 'match' primitive of RD parsers.
            * Increments the global position value
            * Verifies that the current token is of the given type
            * Returns the value of the current token
            * Reads in the next token
        """
        self.cur_pos += 1
        if self.cur_token.type == type:
            val = self.cur_token.val
            self._get_next_token()
            # print("parsing: " + str(val)) # for debugging purposes
            return val
        else:
            if type == ',':
                self._error('Unmatched %s' % type + " . Netstring contents possibly longer than length field indicated."
                            )
            else:
                self._error('Unmatched %s' % type)

    def _netstring(self):
        if self.outer_size > self.cur_pos:
            if self.cur_token.type is None:
                return ''
            elif self.cur_token.type == '0':
                self._match('0')
                number_string = self._digits(True)
                try:
                    container_size = int(float(number_string[:-1]))  # defines the size of the whole netstring container
                    if not container_size == 0:
                        self.leading_zero = True
                    else:
                        self.leading_zero = False
                    if self.outer_flag:
                        self.outer_size = container_size + self.cur_pos + 1
                        self.container_stack.append(self.outer_size)
                        self.outer_flag = False
                except TypeError:
                    print("ERROR! Container size must be numerical!")
                    return ''
                if not container_size + self.cur_pos < self.container_stack[-1]:
                    print("ERROR! Container of size " + str(container_size) +
                          " exceeds upper container boundaries! ")
                    return ''
                if not container_size == 0:
                    number_string = "0" + number_string
                self.container_stack.append(container_size + self.cur_pos)
                nested = number_string + self._netstring()
                return nested
            elif self.cur_token.type == 'NDIGIT':
                self.leading_zero = False
                number_string = self._digits()
                string_size = int(float(number_string[:-1]))
                if len(self.container_stack) > 0:
                    if not string_size + self.cur_pos < self.container_stack[-1]:
                        print("ERROR! Netstring of size " + str(string_size) + " exceeds upper container boundaries!")
                        return ''
                netstring = str(number_string) + str(self._bytestring(string_size))
                if self.outer_size > self.cur_pos:
                    return netstring + self._netstring()
                else:
                    return netstring
            else:
                if self.leading_zero:
                    print("ERROR! Expected another netstring to begin due to leading zero in the upper container.")
                    return ''
                if len(self.container_stack) == 0:
                    print("ERROR! Expected a length-prefix definition at string-position: " str(self.cur_pos-1)))
                    return ''
                self._match(',')
                if not self.container_stack[-1] < self.cur_pos:
                    print("Expected a length prefix definition at string-position: " + str(self.cur_pos-1))
                    return ''
                else:
                    self.container_stack.pop()
                    return ',' + self._netstring()
        else:
            return ''

    def _bytestring(self, size):
        byte_string = ""
        if self.cur_token.type is None:
            return ''
        elif self.cur_token.type == 'BYTE' or self.cur_token.type == 'NDIGIT' or self.cur_token.type == '0' or\
                self.cur_token.type == ',' or self.cur_token.type == ':':
            while self.cur_token.type == 'BYTE' or self.cur_token.type == 'NDIGIT' or self.cur_token.type == '0' or\
                    self.cur_token.type == ',' or self.cur_token.type == ':':
                if self.cur_token.type == 'BYTE':
                    byte_string += str(self._match('BYTE'))
                elif self.cur_token.type == 'NDIGIT':
                    byte_string += str(self._match('NDIGIT'))
                elif self.cur_token.type == '0':
                    byte_string += str(self._match('0'))
                elif self.cur_token.type == ',':
                    byte_string += str(self._match(','))
                elif self.cur_token.type == ':':
                    byte_string += str(self._match(':'))
                size -= 1
                if size == 0:  # acc == 0
                    self._match(',')
                    return byte_string + ','
        else:
            # should never occur. Every byte has to be accepted.
            print("ERROR! invalid byte: " + str(self.cur_token.val))

    def _digits(self, container_flag=False):
        number_string = ""
        if self.cur_token.type is None:
            return ''
        elif container_flag:
            if self.cur_token.type == 'NDIGIT':
                while self.cur_token.type == 'NDIGIT' or self.cur_token.type == '0':
                    if self.cur_token.type == 'NDIGIT':
                        number_string = number_string + str(self._match('NDIGIT'))
                    elif self.cur_token.type == '0':
                        number_string = number_string + str(self._match('0'))
                number_string += self._match(':')
                return number_string
            elif self.cur_token.type == ':':
                return "0" + self._match(':')
        elif self.cur_token.type == 'NDIGIT' or self.cur_token.type == '0':
            while self.cur_token.type == 'NDIGIT' or self.cur_token.type == '0':
                if self.cur_token.type == 'NDIGIT':
                    number_string = number_string + str(self._match('NDIGIT'))
                elif self.cur_token.type == '0':
                    number_string = number_string + str(self._match('0'))
            number_string += self._match(':')
            return number_string


if __name__ == '__main__':
    p = CalcParser()
    # incorrect netstring, container definition needs another netstring inside (parses correctly with error message)
    # print(p.parse("03:abc,"))

    # correct netstring (parses correctly)
    # print(p.parse('024:011:3:abc,2:cd,,5:abcde,,'))

    # incorrect netstring with appended contents after actual netstring (parses correctly only until ',')
    # print(p.parse("3:abc,tgdfr"))

    # incorrect netstring, contents longer than Length Field indicated (parses correctly and throws error after 'c')
    # print(p.parse("3:abcd,"))

    # incorrect netstring, '03'-string does not contain another netstring (parses correctly with correct error message)
    # print(p.parse("07:03:abc,,"))

    # correct netstring, inner '03:abc,' gets parsed as normal character bytestring (parses correctly)
    # print(p.parse("7:03:abc,,"))

    # container "03:abc," too large for outer container with size 4 (parses correctly with error message)
    # print(p.parse("04:03:abc,,"))

    # netstring "4:0000," too large for upper container with size 5 (parses correctly with error message)
    # print(p.parse("05:4:0000,,"))

    # non-numerical container size after leading zero (parses correctly with error message)
    # print(p.parse("07:0a:abc,,"))

    # non-numerical length field (parses correctly and throws error but error message not fitting)
    # print(p.parse("ab:cde,"))

    # correct netstring (parses correctly)
    # print(p.parse("09:2:ad,1:d,,"))

    # correct netstring (with appended contents beyond size), using 0s as >1st letters now works. (parses correctly)
    # print(p.parse("010:3:abc,1:d,,010:3:abc,1:d,,"))

    # correct netstring with appended contents beyond outer size (parses correctly without additional chars)
    # print(p.parse("016:5:hello,5:world,,hjk"))

    # correct netstring with appendix beyond outer size, (parses correctly without the additional '432' chars)
    print(p.parse("0116:053:021:9:abcdefghi,6:abcdef,,23:abcdefghijklmnopqrstuvw,,"
                  "053:24:abcdefghijklmnopqrstuvwx,21:abcdefghijklmnoprstuv,,,432"))

    # incorrect netstring, 022 is 1 too large (parses correctly and throws error at position 34)
    # print(p.parse("0116:053:022:9:abcdefghi,6:abcdef,,23:abcdefghijklmnopqrstuvw,,"
    #              "053:24:abcdefghijklmnopqrstuvwx,21:abcdefghijklmnoprstuv,,,432"))

    # correct string, numbers in bytestring work now (parses correctly)
    # print(p.parse("011:4:5zuo,1:d,,"))

    # correct string, ',' and ':' in bytestrings work now (parses correctly)
    # print(p.parse("09:2:,:,1:,,"))

    # correct empty string (parses correctly)
    # print(p.parse("0:,"))

    # incorrect string, contents of 0-container too large (parses correctly and throws error after ':')
    # print(p.parse("0:a,"))

    # correct string (parses correctly)
    # print(p.parse("03:0:,,"))

    # incorrect string, last 0:, netstring exceeds upper container boundaries (parses correctly and throws error)
    # print(p.parse("07:03:0:,0:,,,"))

    # incorrect string, one comma too much (parses correctly and stops at the first comma)
    # print(p.parse("02:0:,,"))

    # incorrect string, contents of 04-container too short (parses correctly and throws error)
    # print(p.parse("04:0:,,,"))

    # correct string (parses correctly)
    # print(p.parse("06:0:,0:,,"))

    # incorrect string, second 0:, netstring exceeds upper container boundaries (parses correctly and throws error)
    # print(p.parse("05:0:,0:,,"))

    # print(p.parse(",:,"))
    # incorrect string, contents of 07-container too short (parses correctly and throws Error)
    # print(p.parse("07:0:,0:,,,"))

    # correct string (parses correctly)
    # print(p.parse("07:0:,1:d,,"))

    # print(p.parse("00:,"))

    # correct string (parses correctly)
    # print(p.parse("028:03:0:,,06:0:,0:,,07:0:,1:d,,,"))
