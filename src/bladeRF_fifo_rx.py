#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: bladeRF FIFO RX
# Author: Jon Szymaniak <jon.szymaniak@nuand.com>
# Description: RX bladeRF SC16 Q11 samples from a FIFO, convert them to GR Complex values, and write them to a GUI sink.
# GNU Radio version: 3.10.10.0

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from gnuradio import blocks
import pmt
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
import sip



class bladeRF_fifo_rx(gr.top_block, Qt.QWidget):

    def __init__(self, frequency=1e9, sample_rate=2000000):
        gr.top_block.__init__(self, "bladeRF FIFO RX", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("bladeRF FIFO RX")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "bladeRF_fifo_rx")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)

        ##################################################
        # Parameters
        ##################################################
        self.frequency = frequency
        self.sample_rate = sample_rate

        ##################################################
        # Variables
        ##################################################
        self.sample_rate_range = sample_rate_range = sample_rate
        self.frequency_range = frequency_range = frequency

        ##################################################
        # Blocks
        ##################################################

        self._sample_rate_range_range = qtgui.Range(160e3, 40e6, 1e6, sample_rate, 200)
        self._sample_rate_range_win = qtgui.RangeWidget(self._sample_rate_range_range, self.set_sample_rate_range, "Sample Rate", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._sample_rate_range_win, 0, 0, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._frequency_range_range = qtgui.Range(300e6, 3.8e9, 1e6, frequency, 200)
        self._frequency_range_win = qtgui.RangeWidget(self._frequency_range_range, self.set_frequency_range, "Frequency", "counter", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._frequency_range_win, 0, 1, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.qtgui_sink_x_0 = qtgui.sink_c(
            4096, #fftsize
            window.WIN_RECTANGULAR, #wintype
            frequency_range, #fc
            sample_rate_range, #bw
            "", #name
            True, #plotfreq
            True, #plotwaterfall
            True, #plottime
            True, #plotconst
            None # parent
        )
        self.qtgui_sink_x_0.set_update_time(1.0/10)
        self._qtgui_sink_x_0_win = sip.wrapinstance(self.qtgui_sink_x_0.qwidget(), Qt.QWidget)

        self.qtgui_sink_x_0.enable_rf_freq(True)

        self.top_grid_layout.addWidget(self._qtgui_sink_x_0_win, 1, 0, 1, 8)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 8):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.blocks_throttle2_0 = blocks.throttle( gr.sizeof_gr_complex*1, 10e6, True, 0 if "auto" == "auto" else max( int(float(0.1) * 10e6) if "auto" == "time" else int(0.1), 1) )
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_cc((1.0 / 2048.0))
        self.blocks_interleaved_short_to_complex_0 = blocks.interleaved_short_to_complex(True, False,1.0)
        self.blocks_file_source_0 = blocks.file_source(gr.sizeof_short*2, '/home/viktor/Documents/rir/data/bob_rx1_1GHz_1MHz_-40_20.iqbin', True, 0, 0)
        self.blocks_file_source_0.set_begin_tag(pmt.PMT_NIL)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_file_source_0, 0), (self.blocks_interleaved_short_to_complex_0, 0))
        self.connect((self.blocks_interleaved_short_to_complex_0, 0), (self.blocks_throttle2_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.qtgui_sink_x_0, 0))
        self.connect((self.blocks_throttle2_0, 0), (self.blocks_multiply_const_vxx_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "bladeRF_fifo_rx")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_frequency(self):
        return self.frequency

    def set_frequency(self, frequency):
        self.frequency = frequency
        self.set_frequency_range(self.frequency)

    def get_sample_rate(self):
        return self.sample_rate

    def set_sample_rate(self, sample_rate):
        self.sample_rate = sample_rate
        self.set_sample_rate_range(self.sample_rate)

    def get_sample_rate_range(self):
        return self.sample_rate_range

    def set_sample_rate_range(self, sample_rate_range):
        self.sample_rate_range = sample_rate_range
        self.qtgui_sink_x_0.set_frequency_range(self.frequency_range, self.sample_rate_range)

    def get_frequency_range(self):
        return self.frequency_range

    def set_frequency_range(self, frequency_range):
        self.frequency_range = frequency_range
        self.qtgui_sink_x_0.set_frequency_range(self.frequency_range, self.sample_rate_range)



def argument_parser():
    description = 'RX bladeRF SC16 Q11 samples from a FIFO, convert them to GR Complex values, and write them to a GUI sink.'
    parser = ArgumentParser(description=description)
    parser.add_argument(
        "--frequency", dest="frequency", type=eng_float, default=eng_notation.num_to_str(float(1e9)),
        help="Set Frequency [default=%(default)r]")
    parser.add_argument(
        "-s", "--sample-rate", dest="sample_rate", type=eng_float, default=eng_notation.num_to_str(float(2000000)),
        help="Set Sample Rate [default=%(default)r]")
    return parser


def main(top_block_cls=bladeRF_fifo_rx, options=None):
    if options is None:
        options = argument_parser().parse_args()

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls(frequency=options.frequency, sample_rate=options.sample_rate)

    tb.start()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
