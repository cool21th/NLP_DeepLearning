#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 13 11:40:37 2016

@author: georgeyiapanis

 *************************************************************************** 
  * IBM Source Material 
  * (C) COPYRIGHT International Business Machines Corp., 2016. 
  * 
  * The source code for this program is not published or otherwise divested 
  * of its trade secrets, irrespective of what has been deposited with the 
  * U. S. Copyright Office. 
  *************************************************************************** 
"""

import xlrd

class load_xl(object):
    """Loads data from an excel file and corresponding sheet into a dictionary. Assuming a standard table like format
    
    Positional arguments
    --------------------
    file_name: string
        name of excel file to be read
        
    sheet_name: string
        name of sheet to be read
        
    Optional argumens
    --------------------
    row_header: integer
        the row corresponding to the table headers
        default: row_header = 0
        
    Returns
    --------------------
    class object with the following attributes"
        sheet_name: string
            name of sheet
        file_name: string
            name of excel file
        col_headers: list of strings
            the table headers
        data: dictionary
            {header1 : [value1, value2 ...], header2 : [value1, value2..]}  
            
    Example
    --------------------
    sheet = load_xl('scripts_avatar/Dialog/Dialog_Chitchat/CHITCHAT_CONTENT.xls', 'Answer Mapping', row_header=0)
    sheet.file_name #returns the name of the excel file
    sheet.sheet_name #returns the name of the sheet
    sheet.col_headers #returns the name of the coloumn headers
    sheet.data #returns the data as dictoray with head key corresponding to the coloumn headers
    """   
    def __init__(self, file_name, \
                 sheet_name, \
                 row_header=0):
        self.file_name = file_name
        self.sheet_name = sheet_name
        self.__row_header__ = row_header
        self.__workbook__=xlrd.open_workbook(self.file_name)
        self.__sheet__ = self.__workbook__.sheet_by_name(sheet_name)
        self.col_headers = load_xl.__xl_get_row_slice__(self.__sheet__, \
                                                        row_=self.__row_header__,\
                                                        col_start=0, \
                                                        col_end=self.__sheet__.ncols)
        load_xl.__get_cells_by_col__(self)
   
    def __get_cells_by_col__(self):
        self.data={}
        for i, header in enumerate(self.col_headers):
            self.data[header] = load_xl.__xl_get_col_slice__(self.__sheet__, \
                                                              col_=i, \
                                                              row_start=self.__row_header__+1, \
                                                              row_end=self.__sheet__.nrows)
        return self
        
    def __xl_get_col_slice__(sheet, col_=0, row_start=0, row_end=0):
        cells = sheet.col_slice(colx = col_, start_rowx=row_start, end_rowx=row_end)
        list_ = []
        for cell in cells:
            list_.append(cell.value)
        return list_
            

    def __xl_get_cell__(sheet, row=0, col=0):
        cell = sheet.cell(row, col)
        return cell.value         
        
    def __xl_get_row_slice__(sheet, row_=0, col_start=0, col_end=0):
        cells = sheet.row_slice(rowx = row_, start_colx=col_start, end_colx=col_end)
        list_ = []
        for cell in cells:
            list_.append(cell.value)
        return list_
        
    
        
        
