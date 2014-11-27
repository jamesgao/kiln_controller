#include "protocol.h"

char Comm::buffer[BUFFER_LENGTH+1];
int Comm::_nacts;
char Comm::_commands[MAX_ACTIONS];
char* (*Comm::_actions[MAX_ACTIONS])(int, char*);
char Comm::_current_cmd;
int  Comm::_current_len;

Comm::Comm(int addr) {
  Wire.begin(addr);
  Wire.onReceive(_handle_request);
  Wire.onRequest(_handle_response);
}

int Comm::action(char cmd, char* (*func)(int, char*)) {
  if (_nacts >= MAX_ACTIONS)
    return 1;
    
  _actions[_nacts] = func;
  return 0;
}

void Comm::_handle_request(int nbytes) {
  _current_cmd = Wire.read();
  _current_len = nbytes-1;
  for (int i = 0; i < nbytes-1; i++) {
    buffer[i] = Wire.read();
  }
}

void Comm::_handle_response() {
  for (int i = 0; i < MAX_ACTIONS; i++) {
    if (_commands[i] == _current_cmd) {
      _actions[i](_current_len, buffer);
    }
  }
  Wire.write(buffer);
}
