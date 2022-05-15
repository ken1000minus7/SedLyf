import random               

class GridSpoilerGame:
    
    def __init__(self, rickroll = 2, sips = 3):
        
        # Dictionary 
        self.emojiDict = {
            ':rickroll:': '<a:rickroll:975354466649915505>', 
            ':Sip1:': '<:Sip1:975351580167639110>', 
            ':Sip2:': '<:Sip2:975352396848971826>', 
            ':Sip3:': '<:Sip3:975352470438035527>', 
            ':Sip4:': '<:Sip4:975354110876467240>', 
            ':Sip5:': '<:Sip5:975352647064354886>', 
            ':Sip6:': '<:Sip6:975352717440581732>', 
            ':Sip7:': '<:Sip7:975352797027500093>', 
            ':Sip8:': '<:Sip8:975352884013178930>', 
            ':Sip9:': '<:Sip9:975352948030853192>', 
            ':Sip10:': '<:Sip10:975353012417593344>', 
            ':Sip11:': '<:Sip11:975353354458890254>', 
            ':Sip12:': '<:Sip12:975353421651660830>', 
            ':Sip13:': '<:Sip13:975353495031021629>', 
            ':Sip14:': '<:Sip14:975353552874663976>', 
            ':Sip15:': '<:Sip15:975353694369480724>', 
            ':Sip16:': '<:Sip16:975353795682897930>', 
            ':Sip17:': '<:Sip17:975354145286549505>', 
            ':Sip18:': '<:Sip18:975354177364570152>', 
            ':Sip19:': '<:Sip19:975353630397980743>', 
            ':Sip20:': '<:Sip20:975353617450164264>', 
            ':Sip21:': '<:Sip21:975353400470429746>', 
            ':Sip22:': '<:Sip22:975353365905162280>', 
            ':Sip23:': '<:Sip23:975353325790822420>', 
            ':Sip24:': '<:Sip24:975353302311129098>', 
            ':Sip25:': '<:Sip25:975353275228520498>', 
            ':Sip26:': '<:Sip26:975353249404170271>', 
            ':Sip27:': '<:Sip27:975353225131753472>', 
            ':Sip28:': '<:Sip28:975353198430797874>', 
            ':Sip29:': '<:Sip29:975353172510011442>', 
            ':Sip30:': '<:Sip30:975353143665782805>', 
            ':Sip31:': '<:Sip31:975353105682137128>', 
            ':Sip32:': '<:Sip32:975353079870394440>', 
            ':Sip33:': '<:Sip33:975353050329940020>', 
            ':Sip34:': '<:Sip34:975352999390089266>', 
            ':Sip35:': '<:Sip35:975352822809915452>', 
            ':Sip36:': '<:Sip36:975352715351834625>'
        }
        
        self.grid = [[0 for i in range(6)] for j in range(6)]
        self.rickroll = rickroll
        self.sips = sips
        
        if (rickroll + sips < 36 and rickroll + sips > 2):
            return
        
        if (rickroll < 1): self.rickroll = 1
        if (rickroll > 19): self.rickroll = 19
        
        if (sips < 1): self.sips = 1
        if (sips > 17): self.sips = 16

    
    # ------------------------- Emoji Utility Starts
    def __emojify(self, s: str)->str:
        if (s[0] != ":"):
            s = ":" + s
        if (s[-1] != ":"):
            s = s + ":"
            
        return s

    def __spoiler(self, s: str)->str:
        if (s[0] != "|" and s[1] != "|"):
            s = "||" + s
        if (s[-1] != "|" and s[-2] != "|"):
            s = s + "||"
            
        return s
        
    def __spoiler_emojify(self, s: str)->str:
        return self.__spoiler(self.__emojify(s))
    # Emoji Utility Ends ---------------------------    
    
    
    
    # -------------------- Grid Utility Starts 
    def __make_fresh_grid(self)->None:
        base = "Sip"
        
        for i in range(6):
            for j in range(1, 7):
                self.grid[i][j - 1] = self.__emojify(base + str(i * 6 + j))
                
        return self.grid

    def __make_game_grid(self)->None:
        changed = set();
                
        # Add some rickrolls 
        while len(changed) < self.rickroll:
            random_id = random.randint(0, 35)
            changed.add(random_id)
            
            i, j = random_id // 6, random_id % 6
            
            self.grid[i][j] = self.__spoiler_emojify("rickroll")
        
        indexes = [i for i in range(36)]
        random.shuffle(indexes)
        
        # Spoil some sips :big_sip:
        for i in indexes:
            if self.sips == 0:
                break;
                
            if i not in changed:
                self.grid[i // 6][i % 6] = self.__spoiler_emojify(self.grid[i // 6][i % 6])
                self.sips -= 1  
                
    # Directly use "print" function to print the grid (The only function one needs)
    def __str__(self):
        self.__make_fresh_grid()
        self.__make_game_grid()
        
        grid = ""
        
        for row_ele in self.grid:
            for ele in row_ele:
                tmp = ""
                for i in ele:
                    # If number or colon add
                    if i == ":" or (i >= "0" and i <= "9"): 
                        tmp += i
                    
                    # If alphabets add
                    if (i >= "a" and i <= "z") or (i >= "A" and i <= "Z"):
                        tmp += i
                         
                ele = ele.replace(tmp, self.emojiDict[tmp])
                grid += ele
                
            grid += "\n"
        
        return grid