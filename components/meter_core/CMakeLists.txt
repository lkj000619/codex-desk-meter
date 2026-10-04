idf_component_register(SRCS "src/meter_crc.c"
                             "src/meter_parser.c"
                             "src/meter_state.c"
                             "src/feature_imu.c"
                             "src/meter_gui.c"
                       INCLUDE_DIRS "include"
                       REQUIRES json)
