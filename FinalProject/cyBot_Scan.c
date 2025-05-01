/*
 * cyBot_Scan.c
 *
 *  Created on: Apr 14, 2025
 *      Author: jclark15
 */
#include "Timer.h"
#include "servo.h"
#include "ping.h"
#include "adc.h"

// Scan value
typedef struct{
    float sound_dist;  // Distance from PING sensor (cyBOT_Scan returns -1.0 if PING is not enabled)
    int IR_raw_val;    // Raw ADC value from IR sensor (cyBOT_Scan returns -1 if IR is not enabled)
} cyBOT_Scan_t;


void cyBOT_init_Scan(int feature) {
    timer_init();
    ping_init();
    adc_init();
    servo_init();
}

void cyBOT_Scan(int angle, cyBOT_Scan_t* getScan) {
    servo_move(angle);
    getScan->sound_dist = ping_getDistance();
    getScan->IR_raw_val = adc_read();
}
