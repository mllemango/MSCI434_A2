from gurobipy import *
import csv


def info():
    # porting in the static data

    COST_KM = 187

    # plants
    plants = ['cambridge', 'barrie']
    plant_cap = {'cambridge': 1500, 'barrie': 1500}
    plant_cost = {'cambridge': 288.00, 'barrie': 476.00}

    # warehouses
    WHs = []
    WH_cap = {}
    WH_Cost = {}
    with open('WH.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            WH = row[0].lower()
            WHs.append(WH)
            WH_cap[WH] = row[1]
            WH_Cost[WH] = row[2]
    # print(WHs)
    # print(WH_cap)
    # print(WH_Cost)
    # customers
    custs = []
    cust_demand = {}
    with open('cust.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            cust = row[0].lower()
            custs.append(cust)
            cust_demand[cust] = row[1]
    # print(custs)
    # print(cust_demand)

    # distances
    plant_WH_distance = {}
    with open('plant_WH_distance.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for line in csv_reader:
            WH = line[0].lower()
            plant = line[1].lower()
            dist = float(line[2]) * COST_KM
            plant_WH_distance[(plant, WH)] = dist

    # print(plant_WH_distance[('Ottawa', 'Barrie')])

    WH_cust_distance = {}
    with open('WH_cust_distance.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for line in csv_reader:
            cust = line[0].lower()
            WH = line[1].lower()
            if (line[2] == ''):
                dist = 0
            else:
                dist = float(line[2]) * COST_KM
            WH_cust_distance[(WH, cust)] = dist

    # print(WH_cust_distance[('Greater Sudbury', 'London')])

    return plants, WHs, custs, plant_cap, plant_cost, WH_cap, WH_Cost, cust_demand, plant_WH_distance, WH_cust_distance



def optimize(plants, WHs, custs, plant_cap, plant_cost, WH_cap, WH_Cost, cust_demand, plant_WH_distance, WH_cust_distance):
    m = Model()

    # creating variables
    P = len(plants)
    W = len(WHs)
    C = len(custs)
    tij = m.addVars(plants, WHs, vtype=GRB.INTEGER)  # number of goods from plant i to WH j
    Cjk = m.addVars(WHs, custs, vtype=GRB.INTEGER)  # number of goods from WH j to cust k
    Wj = m.addVars(WHs, vtype=GRB.BINARY)  # 1 if warehouse j operates

    # constants
    dij = plant_WH_distance
    djk = WH_cust_distance
    Cj = WH_Cost
    Ci = plant_cost
    Wpj = WH_cap
    Cdk = cust_demand
    Pci = plant_cap  # [1500, 1500]

    print(djk)
    # objective function

    m.setObjective(quicksum(quicksum(tij[i, j] * dij[(i, j)] for i in plants) for j in WHs) +
                   # tij.prod(dij) +
                   quicksum(Wj[j] * Cj[j] for j in WHs) +
                   # Cjk.prod(djk) +
                   quicksum(quicksum(Cjk[j, k] * djk[j, k] for j in WHs) for k in custs) +
                   quicksum(Ci[i] for i in plants), GRB.MINIMIZE)  # last summation is a constant

    # constraints
    # Plant constraints
    for i in plants:
        m.addConstr(quicksum(tij[i, j] for j in WHs) <= Pci[i])  # goods going out of plant i does not go over plant capacity
    # WH constraints --> 1 constraint for each WH
    for j in WHs:
        # m.addConstr(quicksum(tij[i, j] for i in range(P)) <= Wpj[j])  # WH goods do not exceed capcity
        m.addConstr(quicksum(tij[i, j] for i in plants) == quicksum(Cjk[j, k] for k in custs))  # goods going into WH = goods going out of WH
    # Customer demand
    for k in custs:
        cust_k_demand = int(Cdk[k])
        m.addConstr(quicksum(Cjk.sum(j, k, '*') for j in WHs) == cust_k_demand)  # demand is met for Cust K
    # Operations
    for j in WHs:
        m.addConstr(Wj[j] * Wpj[j] - quicksum(tij[i, j] for i in plants) >= 0)  # if WH j is not operating, nothing goes out of it

    m.update()
    m.optimize()

    # printing output
    print('Min Cost', m.objVal)
    solution = m.getAttr('x', Wj)
    print(solution)


if __name__ == "__main__":

    plants, WHs, custs, plant_cap, plant_cost, WH_cap, WH_Cost, cust_demand, plant_WH_distance, WH_cust_distance = info()
    optimize(plants, WHs, custs, plant_cap, plant_cost, WH_cap, WH_Cost, cust_demand, plant_WH_distance, WH_cust_distance)
