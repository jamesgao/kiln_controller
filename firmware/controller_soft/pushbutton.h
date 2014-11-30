class pushbutton : public CallBackInterface
{
  public:
    int n_clicks;
    uint8_t pin;
    unsigned int interval;
    unsigned long last;
    
    pushbutton (uint8_t _pin, unsigned int _interval): pin(_pin) , interval(_interval) {
      dir = 0;
      n_clicks = 0;
      last = 0;
      init();
    };
    void cbmethod() {
      last = millis();
    };
    
    void update() {
      if (last != 0 && (millis() - last) > interval) {
        n_clicks += dir;
        last = 0;
      }
    }
    
    void setDir(int d) {
      dir = d;
    }
  
  private:
    int dir;
    
    void init () {
      pinMode(pin, INPUT);
      digitalWrite(pin, HIGH);
      PCintPort::attachInterrupt(pin, this, CHANGE);
    };
};

