"""bladeRF 2.0 micro xA4 control - Rx side

Quick and simple script to receive a CW tone from a bladeRF 2.0 micro xA4
unit.
"""


import datetime
import logging
import numpy as np

from bladerf import _bladerf

import helpers


NTP_SERVER = "0.uk.pool.ntp.org"


def bladerf_cw_tone_rx(params: dict, logger: logging.Logger) -> None:
    """Sets up a BladeRF 2.0 micro xA4 as a CW receiver

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
        channel = _bladerf.CHANNEL_RX(params["rx_ch"])
        rx_ch = sdr.Channel(channel)
    except Exception as error:
        logger.critical(f"Invalid Rx channel value: {channel}")
        raise RuntimeError("Error configuring bladeRF unit") from error

    logger.info(f"Using Rx channel: {channel}")

    rx_ch.frequency = params["freq_centre"]
    logger.info(f"Rx LO set to {rx_ch.frequency:.3e} Hz")
    
    rx_ch.sample_rate = params["sample_rate"]
    logger.info(f"Rx sample rate set to {rx_ch.sample_rate:.3e} samples/sec")
    
    rx_ch.bandwidth = params["bandwidth"]
    logger.info(f"Rx BW set to {rx_ch.bandwidth:.3e} Hz")
    
    rx_ch.gain_mode = _bladerf.GainMode.Manual
    logger.info("Set gain mode to manual - AGC disabled")
    
    rx_ch.gain = params["rx_gain"]

    sdr.sync_config(
        layout=_bladerf.ChannelLayout(channel),
        fmt=_bladerf.Format.SC16_Q11,
        num_buffers=32,
        buffer_size=4096,
        num_transfers=16,
        stream_timeout=3500
    )

    bytes_per_sample = 4
    buffer = bytearray(params["buffer_size"] * bytes_per_sample)
    
    num_samples = int(params["sample_rate"] * params["time_duration"])
    logging.info(f"Calculated number of samples: {num_samples:.2e}")

    rx_ch.enable = True
    logger.info(f"Rx gain set to {rx_ch.gain} dB")
    logger.info("Rx channel configured and enabled")

    # ! Each sample consists of I and Q values
    rx_signal = np.zeros(num_samples * 2, dtype=np.int16)

    num_samples_rcvd = 0

    with open("test.iqbin", "wb") as out_file:
        while True:
            if num_samples > 0 and num_samples_rcvd == num_samples:
                logging.info("All samples received")
                break
            elif num_samples > 0:
                num = min(
                len(buffer) // bytes_per_sample, num_samples - num_samples_rcvd
                )
            else:
                num = len(buffer) // bytes_per_sample
        
            sdr.sync_rx(buffer, num) 
        
            samples = np.frombuffer(buffer, dtype=np.int16)
        
#        samples = samples[0::2] + 1j * samples[1::2] # Convert to complex type
#        samples /= 2048.0 # Scale to -1 to 1 (its using 12 bit ADC)
            out_file.write(samples.tobytes())
            
#            rx_signal[num_samples_rcvd:num_samples_rcvd+2*num] = samples # Store buf in samples array
        
            num_samples_rcvd += num
            logging.info(f"Received {num_samples_rcvd} out of {num_samples}")


    rx_ch.enable = False
    logger.info("Rx channel disabled")

   
if __name__ == "__main__":
    # args = cli_args()

    global_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    params = {
       "rx_ch": 0,
       "sample_rate": 20e6,
       "freq_centre": 1e9,
       "bandwidth": 10e6, 
       "rx_gain": 0,
       "time_duration": 0.01,
       "buffer_size": 2000
    }

    bladerf_rx_logger = helpers.setup_logger(
        "SAC-SimpleRx", global_timestamp
    )
    helpers.log_ntp_time(bladerf_rx_logger, NTP_SERVER)

    try:
        bladerf_cw_tone_rx(params, bladerf_rx_logger)
    except RuntimeError:
        bladerf_rx_logger.info(
            "Please check the BladeRF is connected to this PC and running"
        )

    logging.shutdown()
