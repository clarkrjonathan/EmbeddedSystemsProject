/*
 * servo.c
 *
 *  Created on: Apr 14, 2025
 *      Author: jclark15
 */
#include <inc/tm4c123gh6pm.h>
#include <stdint.h>
#include "servo.h"
#include "Timer.h"
#include "lcd.h"

uint32_t calibratedLeft = 34650;
uint32_t calibratedRight = 7760;
float currAngle = 90;
int timeMult = 15;
int timeBias = 100;

void servo_init(void)
{
    //on PB5 0b10 0000 or 0x20
    //T1CCP1
    //enable pwm clock by writing a value of 0x00100000 to the RCGC0 register in systctl
    SYSCTL_RCGCGPIO_R |= 0x2;

    //enable clock on port B
    SYSCTL_RCGCTIMER_R |= 0x2;

    //busy wait both GPIO B module and PWM 0 module ready
    while ((SYSCTL_PRGPIO_R & 0x02) == 0)
        ;
    while ((SYSCTL_RCGCTIMER_R & 0x2) == 0)
        ;

    //enable digital functions and alternate functions on PB5
    GPIO_PORTB_DEN_R |= 0x20;
    GPIO_PORTB_AFSEL_R |= 0x20;

    GPIO_PORTB_DIR_R |= 0x20;
    //PCTL encoding 7
    GPIO_PORTB_PCTL_R = (GPIO_PORTB_PCTL_R & 0x0FFFFF) | 0x700000;

    // Disable timer
    TIMER1_CTL_R &= ~(0x100);

    //write gptm cfg
    TIMER1_CFG_R = (TIMER1_CFG_R & 0x0) | 0x4;

    //TBAMS bit to 0x1 TBCMR bit to 0x0 and TBMR field to 0x2
    TIMER1_TBMR_R = (TIMER1_TBMR_R & ~0b1111) | 0b1010;

    //values loaded to 20ms distance between start of pulses
    //load prescale
    TIMER1_TBPR_R = 0x4;

    //load initial val
    TIMER1_TBILR_R = 0xE200;

    TIMER1_TBPMR_R = 0x4;

    TIMER1_TBMATCHR_R = 0xE200;

    //enable timer
    TIMER1_CTL_R |= 0x100;

}

/**
 * Moves to a position in degrees, may not be absolute the position is just based off the datasheet
 */
void servo_move(float degrees)
{
    //generate pulse based on degree
    //wait some delay based on this
    //return

    //find ratio of degrees
    float ratio = 0;
    if(degrees >= 180) {
        ratio = 1;
    } else if (degrees <= 0) {
        ratio = 0;
    } else {
        ratio = (degrees)/180;
    }

    uint32_t correctedPulseLength =(ratio * (calibratedLeft - calibratedRight)) + calibratedRight;

    servo_setPulseLength(correctedPulseLength);
    float time = abs(currAngle - degrees) * timeMult + timeBias;
    timer_waitMillis(time);
    currAngle = degrees;
}

//sets match registers based on pulseLength in clock cycles
void servo_setPulseLength(uint32_t pulseLength)
{
    uint32_t lowPulse = 0x4E200 - pulseLength;

    TIMER1_TBMATCHR_R = (lowPulse & 0xFFFF);
    TIMER1_TBPMR_R = (lowPulse & 0xFF0000) >> 16;
}


void servo_calibrate(void)
{
    //initialize and busy wait port E

    SYSCTL_RCGCGPIO_R |= 0x10;
    while ((SYSCTL_PRGPIO_R & 0x10) == 0)
        ;

    GPIO_PORTE_DEN_R |= 0b111;
    GPIO_PORTE_DIR_R &= 0b000;
    uint32_t pulseLength = 24000;
    uint32_t leftVal = 0;
    uint32_t rightVal = 0;

    //while third button hasn't been pressed 110 & 100
    lcd_printf("Button 1: Left\nButton 2: Right\nPress 3 at 180 degrees");

    while ((GPIO_PORTE_DATA_R & 0b100) > 0)
    {

        if (((GPIO_PORTE_DATA_R & 0b001) == 0) && pulseLength > 6000)
        {
            pulseLength += 50;
        }
        else if (((GPIO_PORTE_DATA_R & 0b010) == 0) && pulseLength < 50000)
        {
            pulseLength -= 50;
        }

        timer_waitMillis(5);
        servo_setPulseLength(pulseLength);
    }

    leftVal = pulseLength;
    pulseLength = 24000;

    lcd_printf("Button 1: Left\nButton 2: Right\nPress 3 at 0 degrees");
    timer_waitMillis(500);
    while ((GPIO_PORTE_DATA_R & 0b100) > 0)
    {

        if (((GPIO_PORTE_DATA_R & 0b001) == 0) && pulseLength < calibratedLeft + 2500)
        {
            pulseLength += 70;
        }
        else if (((GPIO_PORTE_DATA_R & 0b010) == 0) && pulseLength > calibratedRight - 2500)
        {
            pulseLength -= 70;
        }

        timer_waitMillis(5);
        servo_setPulseLength(pulseLength);
    }
    rightVal = pulseLength;

    lcd_printf("Left Value: %d\nRight Value: %d", leftVal, rightVal);
    calibratedRight = rightVal;
    calibratedLeft = leftVal;
}

