"""bladeRF 2.0 micro xA4 control - Tx side

Quick and simple script to generate a CW tone from a bladeRF 2.0 micro xA4
unit.
"""


import datetime
import logging
import numpy as np

from bladerf import _bladerf

import helpers


NTP_SERVER = "0.uk.pool.ntp.org"


def bladerf_cw_tone(params: dict, logger: logging.Logger) -> None:
    """Sets up a BladeRF 2.0 micro xA4 as a CW transmitter

    """
    sdr = _bladerf.BladeRF()
    channel = _bladerf.CHANNEL_TX(params["tx_ch"])
    tx_ch = sdr.Channel(channel)

    time_duration = np.arange(params["num_samples"]) / params["sample_rate"]

    samples = np.exp(1j * 2 * np.pi * time_duration * params["freq_tone"])
    samples = samples.astype(np.complex64)
    samples *= 32767
    samples = samples.view(np.int16)

    buffer = samples.tobytes()

    tx_ch.frequency = params["freq_centre"]
    tx_ch.sample_rate = params["sample_rate"]
    tx_ch.bandwidth = params["bandwidth"]
    tx_ch.gain = params["tx_gain"]

    sdr.sync_config(
        layout=_bladerf.ChannelLayout(channel),
        fmt=_bladerf.Format.SC16_Q11,
        num_buffers=16,
        buffer_size=8192,
        num_transfers=8,
        stream_timeout=3500
    )

    tx_ch.enable = True

    while True:
        try:
            sdr.sync_tx(buffer, params["num_samples"])
           
        except KeyboardInterrupt:
            break

    tx_ch.enable = False

   
if __name__ == "__main__":
    # args = cli_args()

    global_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    params = {
       "num_samples": int(1e6),
       "tx_ch": 0,
       "sample_rate": 10e6,
       "freq_tone": 1e6,
       "freq_centre": 100e6,
       "bandwidth": 5e6, 
       "tx_gain": 0
    }

    bladerf_tx_logger = helpers.setup_logger(
        "SAC-SimpleTx", global_timestamp
    )
    helpers.log_ntp_time(bladerf_tx_logger, NTP_SERVER)

    try:
        bladerf_cw_tone(params, bladerf_tx_logger)
    except RuntimeError:
        bladerf_tx_logger.info(
            "Please check the BladeRF is connected to this PC and running"
        )

    logging.shutdown()
