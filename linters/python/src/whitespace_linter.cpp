#include <iostream>
#include <sstream>
#include <string>

bool isWhitespace(char ch) {
    return (ch == ' ') || (ch == '\n') || (ch == '\t');
}

int main() {
    std::string line;
    std::string program;

    while(std::getline(std::cin, line)) {
        program += line + '\n';
    }

    char prev1 = ' ', prev2 = ' ';
    int charNumber = 0;
    int lineNumber = 1;
    bool success = true;

    for (char ch : program) {
        charNumber++;

        if (prev1 == '=') {
            std::stringstream os;

            os << "Missing space around = at line ";
            os << lineNumber;

            os << ", column ";
            os << charNumber - 1;

            if (!isWhitespace(prev2)) {
                success = false;
                std::cout << os.str() << " - before symbol =" << std::endl;
            }

            if (!isWhitespace(ch)) {
                success = false;
                std::cout << os.str() << " - after symbol =" << std::endl;
            }
        }

        prev2 = prev1;
        prev1 = ch;

        if (ch == '\n') {
            lineNumber++;
            charNumber = 0;
        }
    }

    if (!success) {
        return 1;
    }

    return 0;
}