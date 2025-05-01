/**
 * Driver for ping sensor
 * @file ping.c
 * @author
 */

#include <stdint.h>
#include <inc/tm4c123gh6pm.h>
#include "ping.h"
#include "Timer.h"
#include "driverlib/interrupt.h"
#include "lcd.h"


// Global shared variables
// Use extern declarations in the header file

volatile uint32_t g_start_time = 0;
volatile uint32_t g_end_time = 0;

volatile enum{LOW, HIGH, DONE} g_state = LOW; // State of ping echo pulse
int overflows = 0;

void ping_init (void){

  // YOUR CODE HERE

    //enable clock on port b and busy wait enabling peripherals
    SYSCTL_RCGCGPIO_R |= 0x02;
    SYSCTL_RCGCTIMER_R |= 0x8;
    while ((SYSCTL_PRGPIO_R & 0x02) == 0) {};
    while ((SYSCTL_PRTIMER_R & 0x8) == 0) {};

    // Disable timer
    TIMER3_CTL_R &= ~(0x100);

    //looking at bit 10, CBERIS which is a "capture mode event" on timer B, triggered when
    //0b100 0000 0000
    TIMER3_IMR_R |= 0x400;
    //dont forget to also enable interrupts (see uart-interrupt)
    //clear interrupt flag
    //set interrupt mask GPTMIMR
    //set nvic priority NVIC_PRI1_R
    //enable interrupts for timer 3b which is interrupt 36 register 5

    NVIC_EN1_R |= 0x10;
    //set bits 5:7 to 0
    NVIC_PRI9_R &= 0b00011111;
    //already set up isr function and master enable of interrupts

    IntRegister(INT_TIMER3B, TIMER3B_Handler);

    IntMasterEnable();

    // Configure and enable the timer
    //set run-mode
    //set count direction
    //Input edge time mode
    //USING TIMER 3B

    //set afsel
    //set pctl
    //enable alternate
    //GPIO_PORTB_PCTL_R encoding is 7 0b111
    GPIO_PORTB_AFSEL_R |= 0b1000;
    GPIO_PORTB_PCTL_R |= (GPIO_PORTB_PCTL_R & 0x0FFF) | 0x7000;
    GPIO_PORTB_DEN_R |= 0x8;

    //Pin is PB3
    TIMER3_CFG_R = (TIMER3_CFG_R & 0x0) | 0x4;

    //Enables edge time mode and capture mode and count direction as down
    TIMER3_TBMR_R = (TIMER3_TBMR_R & 0x0) | 0b0111;

    //set event capture to both edges by writing 0x3 to bits 11:10
    TIMER3_CTL_R |= 0b110000000000;

    //also need to factor in the prescale values GPTMTBPR
    TIMER3_TBPR_R |= 0xFF;

    //load timer start value
    TIMER3_TBILR_R |= 0xFFFF;

    //enable timer
    TIMER3_CTL_R |= 0x100;

    //clear interrupt
    TIMER3_ICR_R |= 0x400;
    //busy wait GPTMRIS
    //poll bit 10 cberis
    while(TIMER3_RIS_R & 0x400 == 0){};

}


void ping_trigger (void){
    g_state = LOW;

    // Disable timer
    TIMER3_CTL_R &= ~(0x100);

    //disable timer interrupt
    TIMER3_IMR_R &= ~(0x400);
    // Disable alternate function (disconnect timer from port pin)
    GPIO_PORTB_AFSEL_R &= ~(0b1000);

    //set gpio portb pin3 dir to out
    GPIO_PORTB_DIR_R |= 0b1000;


    // YOUR CODE HERE FOR PING TRIGGER/START PULSE
    GPIO_PORTB_DATA_R &= ~(0x8);
    GPIO_PORTB_DATA_R |= (0x8);
    timer_waitMicros(5);
    GPIO_PORTB_DATA_R &= ~(0x8);

    // Clear an interrupt that may have been erroneously triggered
    TIMER3_ICR_R |= 0x400;
    // Re-enable alternate function, timer interrupt, and timer
    GPIO_PORTB_AFSEL_R |= 0b1000;
    TIMER3_IMR_R |= 0x400;
    TIMER3_CTL_R |= 0x100;
}

void TIMER3B_Handler(void){

  // YOUR CODE HERE
  // As needed, go back to review your interrupt handler code for the UART lab.
  // What are the first lines of code in the ISR? Regardless of the device, interrupt handling
  // includes checking the source of the interrupt and clearing the interrupt status bit.
  // Checking the source: test the MIS bit in the MIS register (is the ISR executing
  // because the input capture event happened and interrupts were enabled for that event?
  // Clearing the interrupt: set the ICR bit (so that same event doesn't trigger another interrupt)
  // The rest of the code in the ISR depends on actions needed when the event happens.

    //need to read the register values into start and end time
    //TIMER3_MIS_R
    //TIMER3_RIS_R

    //clear interrupt
    TIMER3_ICR_R |= 0x400;

    //saving vals early for accuracy


    if(g_state == LOW) {
        g_state = HIGH;
        g_start_time = TIMER3_TBR_R;

    } else if (g_state == HIGH) {
        g_state = DONE;
        g_end_time = TIMER3_TBR_R;


    }
    //if g_state == DONE we ignore, set low next trigger

}

float ping_getDistance (void){
    ping_trigger();

    while(g_state != DONE) {}

    uint32_t pulseLength;
    //overflowed
    if(g_end_time > g_start_time) {
        pulseLength = g_start_time + (0xFFFFFF - g_end_time);
        overflows += 1;
    } else {
        pulseLength = g_start_time - g_end_time;
    }

    float dist = ((float)pulseLength)* 0.001071875;
    float pulseMillis = ((float)pulseLength)/16000;

    return dist;
}
