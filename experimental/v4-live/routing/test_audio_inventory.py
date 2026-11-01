import unittest
from audio_inventory import parse_stream,channel_choices

class InventoryTests(unittest.TestCase):
    def test_separate_capture_playback_formats_and_counts(self):
        data='''audio4c at usb-host, high speed
Playback:
  Interface 1
    Altset 1
    Format: S32_LE
    Channels: 10
    Rates: 48000, 96000
Capture:
  Interface 2
    Altset 1
    Format: S32_LE
    Channels: 18
    Rates: 48000
    Altset 2
    Format: S16_LE
    Channels: 18
    Rates: 44100, 48000
'''
        entries=parse_stream(data)
        self.assertEqual([e['channels'] for e in entries],[10,18,18])
        self.assertEqual([e['direction'] for e in entries],['playback','capture','capture'])
        self.assertEqual(entries[1]['rates'],'48000')
    def test_stereo_choices_cover_all_even_channels(self):
        choices=channel_choices(18,False)
        self.assertEqual(choices[-1]['channels'],[16,17])
        self.assertEqual(len(choices),9)
        self.assertTrue(all('USB' in c['label'] for c in choices))
    def test_mono_choice_includes_last_odd_channel(self):
        self.assertIn({'label':'USB channel 3 (mono)','channels':[2]},channel_choices(3,include_mono=True))
    def test_empty_or_unrelated_descriptor_is_not_guessed(self):
        self.assertEqual(parse_stream(''),[])
        self.assertEqual(parse_stream('Status: Running\nChannels: 18'),[])

if __name__=='__main__':unittest.main()
