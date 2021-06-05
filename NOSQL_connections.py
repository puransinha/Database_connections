

import psycopg2
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import os
import json
from psycopg2.extras import execute_values
from cassandra.policies import RoundRobinPolicy
from cassandra.query import BatchStatement
from cassandra.cluster import Cluster
from ssl import SSLContext, PROTOCOL_TLSv1

from FurnacePTConfig import USER, PASSWORD, HOST, PORT, DATABASE, SCHEMA, DATABASEIP, KEYSPACE
from FurnacePTConfig import CERTFILE_FILE_PATH, KEYFILE_FILE_PATH, TABLE_NAME, ALGORITHM_NAME
from FurnacePTConfig import logger, RESULT_TABLE_NAME, ERROR_DETAILS_TABLE, CONFIG_PARAM_FILE, OVERALL_REPORT_TABLE
from FurnacePTConfig import DATA_AVG_5MIN_COL, DATA_AVG_30MIN_COL, DATA_AVG_60MIN_COL, CONFIG_PARAM_FILE_PATH
from FurnacePTConfig import MIN_5_INTERVAL, MIN_30_INTERVAL, MIN_60_INTERVAL, CONFIG_FOLDER_NAME, CONFIG_TABLE_NAME
from FurnacePTConfig import SOFT_STD_DETAILS_TABLE_NAME, STD_AVG_DATA_DETAILS, RUN_TIME_TAGS_DETAILS, ALGO_TAG


class FurnacePTDBInterface(object):
    '''
    Furnace Performance Tracker Algorithm's  DB interface class
    '''

    def connect_cassandra(self):
        """
        This function will connect to cassandra database and all required
        connection details will be taken from config.py file
        """
        session = None
        cluster = None
        try:

            ssl_context = SSLContext(PROTOCOL_TLSv1)

            ssl_context.load_cert_chain(
                certfile=CERTFILE_FILE_PATH,
                keyfile=KEYFILE_FILE_PATH)

            cluster = Cluster(DATABASEIP, ssl_context=ssl_context,
                              load_balancing_policy=RoundRobinPolicy(),
                              control_connection_timeout=None,
                              port=9042, connect_timeout=1000
                              )
            session = cluster.connect(KEYSPACE)


        except Exception as ex:
            logger.error('Failed to connect Cassandra DB  : {}'.format(str(ex)))
        finally:
            return session, cluster

    def config_check(self):
        cluster = None
        configuration_df = pd.DataFrame()
        try:

            select_query = "SELECT algorithm_name,file_param_name,flag,blobAsText(file_content) as file_content,param_value,type  from {}.{} WHERE " \
                           "algorithm_name = '{}' and flag=1 ALLOW FILTERING;".format(KEYSPACE, CONFIG_TABLE_NAME,
                                                                                      ALGORITHM_NAME)
            session, cluster = self.connect_cassandra()
            latest_df = session.execute(select_query)
            configuration_df = pd.DataFrame(latest_df)
            # dff=pd.DataFrame(latest_df)
            if not configuration_df.empty:
                param_df = configuration_df[configuration_df['type'] == 1]
                config_files_df = configuration_df[configuration_df['type'] == 2]
                batch = BatchStatement()
                insert_user = session.prepare(
                    "INSERT INTO {}.{} (algorithm_name, file_param_name,flag) VALUES (?,?,?)".format(KEYSPACE,
                                                                                                     CONFIG_TABLE_NAME))
                if not param_df.empty:
                    param_list = list(param_df['file_param_name'])
                    param_df = param_df.set_index('file_param_name')
                    config_param_df = pd.read_csv(CONFIG_PARAM_FILE_PATH).set_index('Parameter')

                    for param in param_list:
                        config_param_df.loc[param, 'Value'] = param_df.loc[param, 'param_value']
                        batch.add(insert_user, (ALGORITHM_NAME, param, 0))
                    config_param_df.to_csv(CONFIG_PARAM_FILE_PATH)
                if not config_files_df.empty:
                    for row in config_files_df.itertuples():
                        df_json = json.loads(row[4])
                        df = pd.DataFrame.from_dict(df_json)
                        filename = CONFIG_FOLDER_NAME + os.sep + row[2]
                        df.to_csv(filename, index=False)
                        batch.add(insert_user, (ALGORITHM_NAME, row[2], 0))
                session.execute(batch)
        except Exception as ex:
            logger.error("Error while updating the config files %s", ex)

        finally:
            if cluster:
                cluster.shutdown()

    def readConfigParametersFromDB(self):
        '''
        This method is used to check any configuration parameter or
        configuration file is changed and then if there is any change in
        configuration parameter / file update changed parameters/ files into
        local folder

        Input Parameters:  None
        Returns:  None

        '''

        '''
        Fetch file_param_name,type from DB for which flag is 1
        After updating the changes into local folder, update the flag to 0 
        for those files/parameters got changed
        '''
        session = None
        cluster = None
        try:

            session, cluster = self.connect_cassandra()

            if session == None:
                logger.error("Failed to connect to Cassandra . Could not proceed further....")
                return

            '''
            Check any file / configuration parmeter is updated from user ie flag ==1
            '''

            select_query = "select file_param_name,type,param_value,file_content from {}.{} where flag = 1 and algo_tag = '{}' allow filtering".format(
                KEYSPACE, CONFIG_TABLE_NAME, ALGO_TAG)

            result_data = session.execute(select_query)
            if not result_data:
                logger.info("None of the configuration parameters or files got changed..")
                return

            reset_flag_list = []
            for row_data in result_data:

                if row_data.type == 1:  # Config parameters
                    print(CONFIG_PARAM_FILE)
                    config_param_df = pd.read_csv(CONFIG_PARAM_FILE_PATH)
                    config_param_df = config_param_df.set_index('Parameter')
                    config_param_df.loc[row_data.file_param_name, 'Value'] = row_data.param_value
                    config_param_df.reset_index(level=0, inplace=True)
                    config_param_df.to_csv(CONFIG_PARAM_FILE_PATH, index=False)
                    reset_flag_list.append(row_data.file_param_name)
                else:
                    # File content got changed
                    # print(row_data)
                    file_path = '{}''{}''{}'.format(CONFIG_FOLDER_NAME, os.sep, row_data.file_param_name)
                    # All are CSV files
                    df_json = json.loads(row_data.file_content)
                    df = pd.DataFrame.from_dict(df_json)
                    df.to_csv(file_path, index=False)

            # reset flag
            if reset_flag_list:
                session.execute(
                    "update {}.{} set flag = 0 where file_param_name in {} and algorithm_name = '{}';".format(
                        KEYSPACE, CONFIG_TABLE_NAME, tuple(reset_flag_list), ALGORITHM_NAME))

        except Exception as ex:
            print(ex)
            logger.error("Exception occurred while Fetching Config Data from \
                          Cassandra database for Furnace Performance Tracker Algorithm : {} ".format(str(ex)))


        finally:
            if cluster:
                cluster.shutdown()

    def readInputDataFromDB(self, time_list, input_data_avg_interval, tags_df, furnace_tag):
        """
        This method is used to fetch Furnace Performance Tracker Algorithm's
        average values of tags from DB

        Input Parameters:
            1. time_list    : Specifies the timestamp intervals for which input data set
                              to be fetched from the DB
            2. tags_list    : Contains list of tags for which input data needs to be fetched

            3. input_data_avg_interval : Specifies the input data avg interval period
        Return:
            Returns average values of tags for specified timestamps

        """

        input_data_df = pd.DataFrame()
        session = None
        cluster = None
        try:

            tags_list = tuple(tags_df[furnace_tag].dropna())

            input_data_avg_select = DATA_AVG_5MIN_COL

            if input_data_avg_interval == MIN_30_INTERVAL:
                input_data_avg_select = DATA_AVG_30MIN_COL
            elif input_data_avg_interval == MIN_60_INTERVAL:
                input_data_avg_select = DATA_AVG_60MIN_COL
            session, cluster = self.connect_cassandra()
            latest_data = session.execute(
                "select tag_name as tag_name, input_time,{} as input_values from {} where tag_name in {} and input_time in {};".format(
                    input_data_avg_select, TABLE_NAME, tags_list, time_list))

            if not latest_data:
                logger.error("Failed to fetch input average data from Data base...")
                # return input_data_df
            else:

                latest_data_df = pd.DataFrame(latest_data)

                latest_data_df['TimeStamp'] = pd.to_datetime(latest_data_df['input_time'], unit='ms')

                input_data_df = pd.merge(tags_df[furnace_tag].dropna(),
                                         latest_data_df[['tag_name', 'input_values', 'TimeStamp']],
                                         left_on=furnace_tag, right_on='tag_name', how='left')
                input_data_df = input_data_df.drop(columns='tag_name')
                input_data_df = pd.pivot_table(input_data_df, index='TimeStamp', columns=furnace_tag,
                                               values='input_values', dropna=False).reset_index()
                input_data_df = input_data_df[(['TimeStamp'] + list(tags_df[furnace_tag].dropna()))]
        except Exception as ex:
            logger.error("Exception occurred while Fetching of Data from Cassandra database  : {} ".format(str(ex)))

        finally:
            if cluster:
                cluster.shutdown()

            # input_data_df.to_csv(".\\output\\input_data_103.csv")
            return input_data_df

    def updateResultDataIntoDB(self, result_data):

        '''
        This method id used to update the result values of Furnace Performance
        Tracker algorithm into DB

        Input Parameters:
            1. result_data : Holds all six parameters values

        Returns:

            None
        '''
        connection = None
        cursor = None
        try:
            # print(result_data)
            connection = psycopg2.connect(user=USER,
                                          password=PASSWORD,
                                          host=HOST,
                                          port=PORT,
                                          database=DATABASE)
            cursor = connection.cursor()

            '''
            data contains tags details for each furnace
            ( console_name, equipment_tag, parameter,score,remark,alert_flag,timestamp )
            '''

            postgres_insert_query = """ INSERT INTO public.{} (console_name, equipment_tag,variable,score,remark,\
                                    alert_flag,timestamp ) VALUES %s""".format(RESULT_TABLE_NAME)
            psycopg2.extras.execute_values(cursor, postgres_insert_query, result_data)
            connection.commit()

        except (Exception, psycopg2.Error) as error:
            logger.error("Error occurred while updating Result Details of \
                          Furnace Performance Tracker Algorithm into DB : {} ".format(str(error)))

        finally:
            # closing database connection.
            if connection:
                cursor.close()
                connection.close()

    def handleFurnacePTReportDetails(self, runtime_tag_avg_df, std_avg_df, furnace_tag, timestamp):

        '''
        This method is used to upload  the Furnace Performance Tracker Algorithm's
        std_avg and runtime_tag_avg values into DB

        Input Parameters   :
            1. std_avg_df         - Standard deviation values for tags
            2. runtime_tag_avg_df - This parameter holds the soft tag data details of tags
            3. furnace_tag        - specifies the furnace tag
            4. timestamp          - timestamp value

        Returns:   None

        '''
        session = None
        cluster = None
        try:

            session, cluster = self.connect_cassandra()

            json_data_std_avg = std_avg_df.to_json()
            json_data_soft_tag_details = runtime_tag_avg_df.to_json()

            insert_query_stmt_std = session.prepare("\
                                INSERT INTO {}.{} (parameter,furnace_tag,file_content,\
                                timestamp) values('{}','{}',textAsBlob('{}'),{})".format(KEYSPACE, \
                                                                                         SOFT_STD_DETAILS_TABLE_NAME,
                                                                                         STD_AVG_DATA_DETAILS,
                                                                                         furnace_tag, json_data_std_avg,
                                                                                         timestamp))

            session.execute(insert_query_stmt_std)

            insert_query_stmt_softtags = session.prepare("\
                                INSERT INTO {}.{} (parameter,furnace_tag,file_content,\
                                timestamp) values('{}','{}',textAsBlob('{}'),{})".format(KEYSPACE, \
                                                                                         SOFT_STD_DETAILS_TABLE_NAME,
                                                                                         RUN_TIME_TAGS_DETAILS,
                                                                                         furnace_tag,
                                                                                         json_data_soft_tag_details,
                                                                                         timestamp))

            session.execute(insert_query_stmt_softtags)
        except Exception as ex:
            logger.error("Eexception occurred while inserting std average soft tag details into \
                          Cassandra database for Furnace Performance Tracker Algorithm : {} ".format(str(ex)))

        finally:
            if cluster:
                cluster.shutdown()

    def updateOverallReportIntoDB(self, overall_output_list):
        '''
        This method id used to update the overall report values of Furnace Performance
        Tracker algorithm into DB

        Input Parameters:
            1. overall_output_list : Holds all six parameters values

        Returns:

            None
        '''
        connection = None
        cursor = None
        try:
            # print(overall_output_list)
            connection = psycopg2.connect(user=USER,
                                          password=PASSWORD,
                                          host=HOST,
                                          port=PORT,
                                          database=DATABASE)
            cursor = connection.cursor()
            print(overall_output_list)
            '''
            data contains tags details for each furnace
            ( console_name, equipment_tag, tag_name,mv,mvmm,cv,cti,timestamp )
            '''

            postgres_insert_query = """ INSERT INTO public.{} (console_name, equipment_tag,tag_name,mv,mvmm,cv,cti,\
                                                timestamp ) VALUES %s""".format(OVERALL_REPORT_TABLE)
            psycopg2.extras.execute_values(cursor, postgres_insert_query, overall_output_list)
            connection.commit()

        except (Exception, psycopg2.Error) as error:
            logger.error("Error occurred while updating Overall reports details of \
                          Furnace Performance Tracker Algorithm into DB : {} ".format(str(error)))

        finally:
            # closing database connection.
            if connection:
                cursor.close()
                connection.close()

    def updateErrorDetailsIntoDB(self, error_result_data):
        '''
        This method is used to insert the error details like offline,data stuck
        of the Furnace Performance Tracker Algorithm into DB table

        Input Parameters   :
            1.  error_result_data  - This parameter holds the tags and error code
            details of Furnace Performance Tracker Algorithm

        Returns:   None

        '''
        connection = None
        cursor = None
        try:
            connection = psycopg2.connect(user=USER,
                                          password=PASSWORD,
                                          host=HOST,
                                          port=PORT,
                                          database=DATABASE)
            cursor = connection.cursor()
            # print(error_result_data)

            '''
            data contains tags details for each furnace
            ( console_name, equipment_tag,algo_tag, tag_name,error_code, timestamp )
            '''

            postgres_insert_query = """ INSERT INTO {}.{} (console_name, equipment_tag,algo_tag,tag_name ,\
                                                error_code,timestamp ) VALUES %s""".format(SCHEMA, ERROR_DETAILS_TABLE)
            psycopg2.extras.execute_values(cursor, postgres_insert_query, error_result_data)
            connection.commit()

        except (Exception, psycopg2.Error) as error:
            logger.error("Error occurred while updating error code details of \
                          Furnace Performance Tracker Algorithm into DB : {} ".format(str(error)))

        finally:
            # closing database connection.
            if connection:
                cursor.close()
                connection.close()


