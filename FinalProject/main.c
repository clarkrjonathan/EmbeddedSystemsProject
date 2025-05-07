/**
 *
 *
 * @author Jonathan Clark
 *
 */

#include "Timer.h"
#include "lcd.h"
#include "cyBot_Scan.h"  // For scan sensors
#include "uart-interrupt.h"
#include <stdbool.h>
#include "driverlib/interrupt.h"
#include "open_interface.h"
#include "math.h"
#include "servo.h"
// #include "button.h"

typedef struct
{
    uint8_t obj_num;
    double obj_angle;
    uint8_t obj_width;
    float obj_dist;

} obj_def_t;


//utility vector struct, if the vector is polar x is theta and y is r
typedef struct
{
    float x;
    float y;
    int isPolar;
} vector;

// Your code can use the global variables defined in uart-interrupt.c
// They are declared with the extern qualifier in uart-interrupt.h, which makes the variables visible to this file.

#define cliff_left 1
#define cliff_front 2
#define cliff_right 3
#define boundry_left 4
#define boundry_front 5
#define boundry_right 6
#define M_PI 3.14159265358979323846
#define speed 150
#define distCorrection 1

void send_string_gui(const char *message);
int checkForCliffs(oi_t *cybot);
void sendScan(cyBOT_Scan_t scan_data[], int numPoints);
void send_string_putty(const char *message);
float getIRDist(float rawIR);
vector toCart(vector v);
vector addVector (vector a, vector b);
void sendIRPoints(cyBOT_Scan_t scan_data[], int numPoints, vector cybotPos, float cybotAngle);
vector getAbsolutePoint(vector point, vector cybotPos, float cybotAngle);
vector toPolar(vector v);
void move(int leftWheel, int rightWheel);


extern volatile char command_byte;
extern volatile int command_flag;

float trim = 0.9809;

int main(void)
{
    timer_init();
    lcd_init();
    uart_interrupt_init();

    oi_t *cybot = oi_alloc();
    oi_init(cybot);
    oi_update(cybot);
    cyBOT_init_Scan();

    servo_moveNonBlocking(0);

    int cliffStatus = 0;

    int firstCliffTrigger = 1;
    int firstBumpTriggerRight = 1;
    int firstBumpTriggerLeft = 1;

    int currAngle = 0;
    int scanning = 0;

    vector cybotPos;
    cybotPos.isPolar = 0;
    cybotPos.x = 0;
    cybotPos.y = 0;
    float cybotAngle = 0;
    int loopCount = 0;

    cyBOT_Scan_t scan_data[200];

    while (1)
    {
        loopCount += 1;

        //every loop before we update we should add our movement vector changes
        //we should only have a change in distance or a change in angle not both
        //only change in either of these when our command changes



        vector movement;

        cybotAngle -= cybot->angle;
        float distTraveled = cybot->distance * (distCorrection);

        movement.x = cybotAngle;
        movement.y = distTraveled;
        movement.isPolar = 1;

        cybotPos = addVector(movement, cybotPos);

        //roll over angle just because it looks nicer
        if(cybotAngle > 360) {
            cybotAngle -= 360;
        } else if(cybotAngle < 0) {
            cybotAngle += 360;
        }

        if(loopCount % 1 == 0) {
            char message[50];
            sprintf(message, "Position:\n%.2f, %.2f, %.2f\n", cybotPos.x, cybotPos.y, cybotAngle);
            send_string_gui(message);
        }



        oi_update(cybot);
        //need to check sensor data first and foremost
        cliffStatus = checkForCliffs(cybot);


        //cliff sensor handling
        if (((cliffStatus == (cliff_left)) || (cliffStatus == (cliff_right)))
                || (cliffStatus == (cliff_front)))
        {
            //hole found
            if(firstCliffTrigger) {
                command_byte = 'I';
                send_string_gui("I");

                if(cliff_left) {
                    send_string_gui("Hole Left");
                } else if (cliff_right) {
                    send_string_gui("Hole Right");
                } else if (cliff_front) {
                    send_string_gui("Hole Front");
                }

                firstCliffTrigger = 0;
            }


        } else if (((cliffStatus == (boundry_left)) || (cliffStatus == (boundry_right)))
                || (cliffStatus == (boundry_front))) {
            //boundry found
            if(firstCliffTrigger) {
                command_byte = 'I';
                send_string_gui("I");

                if(cliffStatus == boundry_left) {
                    send_string_gui("Boundary Left");
                } else if (cliffStatus == boundry_right) {
                    send_string_gui("Boundary Right");
                } else if (cliffStatus == boundry_front) {
                    send_string_gui("Boundary Front");
                }

                firstCliffTrigger = 0;
            }


        } else {
            firstCliffTrigger = 1;
        }

        //bump sensor handling
        if(cybot->bumpLeft && firstBumpTriggerLeft == 1) {
            command_byte = 'I';
            send_string_gui("I");
            send_string_gui("Bumped Left");

            firstBumpTriggerLeft = 0;

        } else if (!(cybot->bumpLeft)) {
            firstBumpTriggerLeft = 1;
        }

        //bump sensor handling
        if(cybot->bumpRight && firstBumpTriggerRight == 1) {
            command_byte = 'I';
            send_string_gui("I");
            send_string_gui("Bumped Right");

            firstBumpTriggerRight = 0;

        } else if (!(cybot->bumpRight)){
            firstBumpTriggerRight = 1;
        }


        //don't do time consuming operations within each loop, we need to be free to recieve next data

        if(command_flag) {

            command_flag = 0;
        }


        switch(command_byte) {
        case 'W':
            move(speed, speed);
            scanning = 0;
            break;

        case 'S':
            move(-speed,-speed);
            scanning = 0;
            break;

        case 'A':
            move(speed, -speed);
            scanning = 0;
            break;

        case 'D':
            move(-speed , speed);
            scanning = 0;
            break;

        case '_':
            move(0, 0);
            if(scanning == 0) {
                scanning = 1;
                currAngle = 0;
            }


            break;

        case 'L':
            if(trim > .001) {
                trim -= .001;
            }

            char trimMessage[20];
            sprintf(trimMessage, "Trim: %f", trim);
            send_string_gui(trimMessage);
            command_byte = 'I';
            break;

        case 'R':
            trim += .001;
            sprintf(trimMessage, "Trim: %f", trim);
            send_string_gui(trimMessage);
            command_byte = 'I';
            break;

        default:
            move(0, 0);
            break;

        }

        if(scanning) {
            if(currAngle > 180) {


                sendScan(scan_data, 180);
                sendIRPoints(scan_data, 180, cybotPos, cybotAngle);
                scanning = 0;
                command_byte = 'I';
                servo_moveNonBlocking(0);
            } else {
                cyBOT_Scan(currAngle, &scan_data[currAngle]);
                if(currAngle % 10 == 0) {
                    char message[20];

                    sprintf(message, "Angle: %d", currAngle);
                    send_string_gui(message);
                }
                currAngle += 1;
            }

        }


    }

}

void send_string_putty(const char *message) {
    int i = 0;

    // Send each character
    for (i = 0; i < strlen(message); i++) {
        uart_sendChar(message[i]);
    }

}

float getIRDist(float rawIR) {
    float a = 9561.29;
    float exp = -0.54574;

    return pow(rawIR/a, 1/exp);
}

void sendScan(cyBOT_Scan_t scan_data[], int numPoints) {
    uart_sendChar(0b110);

    send_string_putty("Scan:\n");
    send_string_putty("14000, 150, 150, 80");

    char message[50];

    int i;
    for(i = 0; i < numPoints - 1;i++) {
        sprintf(message, "%d, %.2f, %.2f, %d\n", scan_data[i].IR_raw_val, getIRDist(scan_data[i].IR_raw_val), scan_data[i].sound_dist, i);
        send_string_putty(message);
    }

    uart_sendChar(0b0);

}

//all units are millimeters
void sendIRPoints(cyBOT_Scan_t scan_data[], int numPoints, vector cybotPos, float cybotAngle) {
    float irDist;
    int i;
    uart_sendChar(0b110);
    send_string_putty("Field:\n");

    char message[50];
    sprintf(message, "170, %.2f, %.2f, %.2f\n", cybotPos.x, cybotPos.y, cybotAngle);
    send_string_putty(message);

    for(i = 0; i < numPoints; i++) {
        irDist = getIRDist(scan_data[i].IR_raw_val) * 10;
        if(irDist < 500) {
            //make sure its within the sensors range or we will just paint walls
            vector point;
            point.isPolar = 1;
            point.x = i;
            point.y = irDist;

            point = getAbsolutePoint(point, cybotPos, cybotAngle);

            char message[50];
            sprintf(message, "%.2f, %.2f, %.2f\n", 20.0, point.x, point.y);
            send_string_putty(message);
        }

    }
    //For some reason its throwing a system interrupt here I need to find where its doing that, whats strange is it lets me finish out the function before going to fault isr

    uart_sendChar(0b0);

}

vector getAbsolutePoint(vector point, vector cybotPos, float cybotAngle) {



    //point is in polar
    point.y += 45;

    point = toCart(point);

 //   add y dist to center
    point.y += 110;

    //rotate by cybot angle
    point = toPolar(point);

    //adjusting for 0 degrees being at -90 relative to cybot

    point.x += cybotAngle;

    //shift by cybots position
    point = toCart(point);
    point = addVector(cybotPos, point);

    return point;

}

//adds the first vector to the second, maintains the coordinate system of the second
//x is theta and y is r
vector addVector (vector a, vector b) {
    vector newVector;
    newVector.isPolar = b.isPolar;

    if(a.isPolar == b.isPolar) {
        newVector.x = a.x + b.x;
        newVector.y = a.y + b.y;
    } else if(b.isPolar == 0) {
        //adding a vector to a non polar vector
        if(a.isPolar) {
            vector aCart = toCart(a);
            newVector.x = b.x + aCart.x;
            newVector.y = b.y + aCart.y;
        }

    }

    return newVector;
}

//takes a polar vector and makes it cartesian
vector toCart(vector v) {
    if(v.isPolar == 0) {
        return v;
    }

    float newX = cos((((float) v.x)/180) * M_PI) * v.y;
    float newY = sin((((float) v.x)/180) * M_PI) * v.y;
    vector newVector;
    newVector.x = newX;
    newVector.y = newY;
    newVector.isPolar = 0;
    return newVector;

}

vector toPolar(vector v) {
    if(v.isPolar) {
        return v;
    }

    float angle;

    angle = atan2(v.x, v.y);

    angle = ((angle/M_PI) * 180);

    float dist = sqrt((v.x * v.x) + (v.y * v.y));
    vector newVector;

    newVector.x = angle;
    newVector.y = dist;
    newVector.isPolar = 1;

    return newVector;
}

int checkForCliffs(oi_t *cybot)
{
    float raw_left = cybot->cliffLeftSignal;
    float raw_right = cybot->cliffRightSignal;
    float raw_frontleft = cybot->cliffFrontLeftSignal;
    float raw_frontright = cybot->cliffFrontRightSignal;

    if ((raw_frontleft < 100) || (raw_frontright < 100))
    {

        return cliff_front;
    }
    else if (raw_left < 100)
    {
        return cliff_left;
    }
    else if (raw_right < 100)
    {
        return cliff_right;
    }
    else if ((raw_frontleft > 2400) || (raw_frontright > 2400))
        {

            return boundry_front;
        }
    else if (raw_left > 2400)
    {
        return boundry_left;
    }
    else if (raw_right > 2400)
    {
        return boundry_right;
    }
    else
    {
        return 0; // all clear no boundries or holes
    }
}

void move(int rightWheel, int leftWheel) {
    oi_setWheels(rightWheel * (1/trim), leftWheel * (trim));
}

void send_string_gui(const char *message)
{
    int i = 0;

// Send each character
    uart_sendChar(0b110);
    for (i = 0; i < strlen(message); i++)
    {
        uart_sendChar(message[i]);
    }
    uart_sendChar(0b0);

}

