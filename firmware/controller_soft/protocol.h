#ifndef PROTOCOL_H
#define PROTOCOL_H

#include "Wire.h"

#define MAX_ACTIONS 16

class Comm {
  private:
    static char buffer[BUFFER_LENGTH+1];
    static int _nacts;
    static char _commands[MAX_ACTIONS];
    static char* (*_actions[MAX_ACTIONS])(int, char*);
    static char _current_cmd;
    static int  _current_len;
    
    static void _handle_request(int);
    static void _handle_response(void);
  
  public:
    Comm(int addr);
    int action(char, char* (*)(int, char*));
};

#endif //PROTOCOL_H
