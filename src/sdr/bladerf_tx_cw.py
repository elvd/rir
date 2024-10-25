"""bladeRF 2.0 micro xA4 control - Tx side

Quick and simple script to generate a CW tone from a bladeRF 2.0 micro xA4
unit.
"""


import datetime
import logging
import numpy as np
import matplotlib.pyplot as plt

from bladerf import _bladerf

import helpers


NTP_SERVER = "0.uk.pool.ntp.org"


def bladerf_cw_tone_tx(params: dict, logger: logging.Logger) -> None:
    """Sets up a BladeRF 2.0 micro xA4 as a CW transmitter

    """
    
    try:
        sdr = _bladerf.BladeRF()
    except Exception as error:
        logger.critical(f"Could not connect to bladeRF unit")
        logger.critical(f"Error message returned: {error.args[0]}")
        raise RuntimeError("Could not connect to bladeRF unit") from error
        
    logger.info(f"Device info: {_bladerf.get_device_list()[0]}")
    logger.info(f"libbladeRF version: {_bladerf.version()}")
    logger.info(f"Firmware version: {sdr.get_fw_version()}")
    logger.info(f"FPGA version: {sdr.get_fpga_version()}")
        
    try:
        channel = _bladerf.CHANNEL_TX(params["tx_ch"])
        tx_ch = sdr.Channel(channel)
    except Exception as error:
        logger.critical(f"Invalid Tx channel value: {channel}")
        raise RuntimeError("Error configuring bladeRF unit") from error

    logger.info(f"Using Tx channel: {channel}")

    tx_ch.frequency = params["freq_centre"]
    logger.info(f"Tx LO set to {tx_ch.frequency:.3e} Hz")
    
    tx_ch.sample_rate = params["sample_rate"]
    logger.info(f"Tx sample rate set to {tx_ch.sample_rate:.3e} samples/sec")
    
    tx_ch.bandwidth = params["bandwidth"]
    logger.info(f"Tx BW set to {tx_ch.bandwidth:.3e} Hz")
    
    tx_ch.gain = params["tx_gain"]
    logger.info(f"Tx gain set to {tx_ch.gain} dB")

    sdr.sync_config(
        layout=_bladerf.ChannelLayout(channel),
        fmt=_bladerf.Format.SC16_Q11,
        num_buffers=512,
        buffer_size=4096,
        num_transfers=32,
        stream_timeout=3500
    )

    time_duration = np.arange(params["num_samples"]) / params["sample_rate"]
    logger.info(f"Calculated signal duration: {np.max(time_duration):.2e} sec")

    samples = np.exp(1j * 2 * np.pi * time_duration * params["freq_tone"])

    #samples = samples.astype(np.complex64)  # TODO: check this
    samples *= 2047

    #samples = samples.view(np.int16)
    samples = np.vstack((samples.real, samples.imag)).reshape((-1,), order='F')
    samples = samples.astype(np.int16)

    logger.info(f"Size of buffer, samples: {np.size(samples):.2e}")

    buffer = samples.tobytes()
    logger.info(f"Size of buffer, bytes: {len(buffer):.2e}")

    tx_ch.enable = True
    logger.info("Tx channel configured and enabled")

    transmit_counter = 0

    while True:
        try:
            sdr.sync_tx(buffer, params["num_samples"])
            transmit_counter += 1
            # logger.info(f"Transmitted {transmit_counter} buffers")
           
        except KeyboardInterrupt:
            logger.info("User interrupt, stopping transmitting")
            break

    tx_ch.enable = False
    logger.info("Tx channel disabled")

   
if __name__ == "__main__":
    # args = cli_args()

    global_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    params = {
       "num_samples": int(1e6),
       "tx_ch": 1,
       "sample_rate": 5e6,
       "freq_tone": 1e6,
       "freq_centre": 1e8,
       "bandwidth": 20e6, 
       "tx_gain": 40
    }

    bladerf_tx_logger = helpers.setup_logger(
        "SAC-SimpleTx", global_timestamp
    )
    helpers.log_ntp_time(bladerf_tx_logger, NTP_SERVER)

    try:
        bladerf_cw_tone_tx(params, bladerf_tx_logger)
    except RuntimeError:
        bladerf_tx_logger.info(
            "Please check the BladeRF is connected to this PC and running"
        )

    logging.shutdown()
