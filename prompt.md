## Complete Project Summary

### 🎯 **Project Goal**
Build a comprehensive tournament management system for CoderCombat competitions that integrates with DOMjudge to manage a complex 8-round tournament with 48 teams.

---

## 📋 **Technical Architecture**

### **Core Technologies**
- **Python 3.9+** with interactive console menus (no CLI)
- **MariaDB/MySQL** with PyMySQL (raw SQL only, no ORM)
- **DOMjudge 8.2** integration via API + direct database access
- **Configuration**: Python constants (no JSON files)

### **System Components**
1. **MenuSystem**: Interactive console menus
2. **DatabaseManager**: Raw SQL for tournament database  
3. **DOMjudgeDBManager**: Direct SQL on DOMjudge database
4. **DOMjudgeAPI**: REST API client for available operations
5. **TournamentEngine**: Main tournament logic and state management
6. **ContestProcessor**: Results processing and team advancement

### **Database Strategy**
- **Tournament DB**: Store domjudge_team_id, domjudge_contest_id for mapping
- **DOMjudge DB Access**: Modify `contestteam` table and `contest.open_for_all_teams` column
- **No backup/restore** functionality needed initially

---

## 🏆 **Tournament Rules**

### **Contest Types**
1. **Duel**: 3 problems, 50min → Winner: Most solved → Least time → Earliest first solve → Most test cases → Coin flip
2. **Group**: 4 problems, 50min, ICPC-style ranking
3. **Speed**: 5 problems, 50min → Only first solver gets 1 point per problem

### **8-Round Structure**
- **R1**: 48 teams → 24 duels → 24W to winners league, 24L to losers league
- **R2**: Winners: 12 duels, Losers: 1 group → Top 4 from group to winners
- **R3**: Winners: 8 duels, Losers: 1 group → Bottom 24 eliminated (ranks 25-48)
- **R4**: Winners: 4 duels, Losers: 1 group + Speed contest for eliminated
- **R5**: Winners rest, Losers: 1 group + Speed contest
- **R6**: 4 duels between promoted losers vs winners
- **R7**: Winners: 2 semi-finals, Losers: 1 group for ranks 5-8
- **R8**: Final + 3rd place playoff

---

## 🎮 **Menu System Design**

### **Main Menu**
```
🏆 CoderCombat Tournament Management System
1. Setup & Configuration
2. Tournament Control  
3. Monitoring & Reports
4. System Tools
5. Exit
```

### **Tournament Control** (Core Workflow)
```
Current State: Round X - Phase Y
1. ▶️  Start Tournament (Round 1)
2. 📊 Process Round Results  
3. ✅ Activate Next Round
4. 🔍 Check Contest Status
5. ⚙️  Manual Adjustments
6. 📈 View Tournament Brackets
7. 🔙 Back to Main Menu
```

---

## ⚡ **Critical Workflow Between Rounds**

### **Contest State Management**
1. **Created**: activation_time = +2 days (invisible to teams)
2. **Activated**: activation_time = now (visible, not started)  
3. **Started**: start_time reached (contest running)
4. **Finished**: Results available for processing

### **Round Transition Process**
1. **Start Tournament/Round**: 
   - Place teams in contests
   - Set activation_time = now
   - Ask user for start_time + delays
   
2. **Process Results** (Manual trigger):
   - Check all current round contests finished
   - Process by contest type (Duel/Group/Speed)
   - Calculate team advancements using graph mapping
   - Place teams for next round (but don't activate)
   
3. **Activate Next Round** (After tech team approval):
   - Set activation_time = now for next round contests
   - Ask for start_time
   - Contests become active

---

## 🗺️ **Team Movement Logic**

### **Graph-Based Mapping** (Option B chosen)
```python
CONTEST_FLOW = {
    "R1_Duel_01": {
        "winner_to": "R2_Duel_01", 
        "loser_to": "R2_Group_Losers"
    },
    "R2_Group_Losers": {
        "rank_1_to_4_go_to": ["R3_Duel_01", "R3_Duel_02", ...],
        "rank_5_plus_go_to": "R3_Group_Losers"
    }
}
```

### **Pairing Rules** (Based on your diagram)
- **Duel Winners**: Specific predetermined pairings (R1_Duel_01 winner vs R1_Duel_02 winner)
- **Group Distribution**: Best performer → Duel_01, second → Duel_02, etc.
- **Speed Contests**: Run simultaneously in R4 and R5 for eliminated teams

### **Contest Naming Convention**
```
R1_Duel_01 to R1_Duel_24
R2_Group_Losers, R2_Duel_01 to R2_Duel_12  
R4_Speed_Eliminated, R5_Speed_Eliminated
R8_Final, R8_Third_Place
```

---

## 🔧 **Implementation Preferences**

- **Step-by-step development** with testing after each component
- **Raw SQL queries** with detailed explanations  
- **Modular, testable code structure**
- **Console-based interactive menus** (no CLI arguments)
- **Manual batch processing** between rounds
- **Graph-based team movement** mapping
- **Validation** of team counts and contest states
- **No password management** for teams

---

## ❓ **Clarification Needed**
- Exact duel pairing patterns from your diagram
- Group-to-multiple-duels distribution order
- Speed contest result processing (rankings only)

**Are we aligned on everything? Should I start implementing the database setup and basic menu system as Step 1?**