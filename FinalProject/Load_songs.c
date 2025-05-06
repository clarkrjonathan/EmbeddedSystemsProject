void loadsongs(void){
unsigned char mcdonald_notes [12] = {67, 67, 67, 62, 64, 64, 62, 71, 71 ,69, 69, 67};// in tune old mcdonald
unsigned char mcdonald_note_duration[12] =  {32, 32, 32, 32, 32, 32, 64, 32, 32, 32, 32, 96}; //note duration for old mcdonald

unsigned char junglebeat_notes[15] = {71, 69, 67, 67, 69, 71, 71, 71, 69, 69, 69, 71, 69, 67, 67};
unsigned char junglebeat_note_duration[15] = {32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 64};

unsigned char twinkle_notes[16] = {67, 67, 74, 74, 76, 76, 74, 71, 71, 69, 69, 67, 76, 76, 74, 74};
unsigned char twinkle_durations[16] = {32, 32, 32, 32, 32, 32, 64, 32, 32, 32, 32, 64, 32, 32, 32, 64};

unsigned char rowboat_notes[16] = {67, 69, 71, 72, 72, 72, 71, 69, 67, 67, 67, 69, 69, 67, 67, 67};
unsigned char rowboat_note_duration[16] = {32, 32, 32, 32, 32, 32, 64, 32, 32, 32, 32, 32, 32, 64, 32, 32};
// song 1 = old mcdonaold
// song 2 ai generated something
//song 3 twinkle twinke little star
//song 4 row row row your boat


oi_loadSong(1, 12, mcdonald_notes, mcdonald_note_duration);
oi_loadSong(2, 15, junglebeat_notes,junglebeat_note_duration);
oi_loadSong(3, 16, twinkle_notes,twinkle_durations);
oi_loadSong(4,16,rowboat_notes,rowboat_note_duration);
// to play song use function oi_play_song(1-4);
}
