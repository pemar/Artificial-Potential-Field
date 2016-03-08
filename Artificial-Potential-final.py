import cv2
import numpy as np
import copy
import glob
import math
import time
from time import sleep
import Queue as Q


images = glob.glob('*.jpg')
def check_boundaries(ex, ey, nx, ny): #ex, ey :- end points of frame
    if nx > -1 and ny > -1 and nx < ex and ny < ey:
        return True
    else:
        return False

def printx(x):
    #print x
    pass

def check_obstacles(arr, ansx, ansy):  #function to check whether a given point is on obstacle or not
    if arr[ansx][ansy][0] == 255:
        return True
    else:
        return False

def feasible(arr, x, y):  #function to check if a point is feasible or not
    ex, ey, ez = arr.shape
    x = int(x)
    y = int(y)

    if check_boundaries(ex, ey, x, y):
        return not check_obstacles(arr, x, y)
    else:
        return False

def dist(sx, sy, x, y, theta, arr, q_star):  #distance of obstacle in direction theta in radians
    ansx = sx
    ansy = sy
    flag = True
    count = 1
    while True:
        if count > q_star:
            return (-1, -1)
        ansx = sx + count*math.sin(theta)
        ansy = sy + count*math.cos(theta)

        if check_boundaries(x, y, ansx, ansy) == False:
            break
        else:
            if check_obstacles(arr, ansx, ansy) == True:
                break
        count += 1

    return (ansx-sx,ansy- sy)



def obstacle_force(arr, sx, sy, q_star): #sx,sy :- source    dx, dy:- destination    q-star:- threshold distance of obstacles
    forcex = 0
    forcey = 0
    neta = 30000
    x, y , z= arr.shape
    for i in range(8):
        (ox,oy) = dist(sx, sy, x, y, i*math.pi/4, arr, q_star)
        theta = i*math.pi/4
        ox = math.fabs(ox)
        oy = math.fabs(oy)

        d = math.hypot(ox,oy)
        fx = 0
        fy = 0
        if ox == -1 or oy == -1:
            fx = 0
            fy = 0
        else:
            if d == 0:
                d = 1
            f = (neta*(1.0/q_star- 1.0/d))/(d*d)
            fx = f*math.sin(theta)
            fy = f*math.cos(theta)

        forcex += fx
        forcey += fy

    return (forcex, forcey)

def goal_force(arr, sx, sy, dx, dy, d_star): # sx, sy :- source  dx, dy:- destination   d_star:- threshold distance from goal
    forcex = 0
    forcey = 0
    tau = 1  #constant
    printx('10')
    d = math.sqrt((dx-sx)*(dx-sx) + (dy-sy)*(dy-sy))
    if d > d_star:
        forcex += ((d_star*tau*math.sin(math.atan2(dx-sx, dy-sy))))
        forcey += ((d_star*tau*math.cos(math.atan2(dx-sx, dy-sy))))

    else:
        forcex += ((dx-sx)*tau)
        forcey += ((dy-sy)*tau)

    printx('11')
    return (forcex, forcey)

def path_planning(arr, sx1, sy1, dx, dy):
    '''

    :param arr: input map
    :param sx1: source x
    :param sy1: source y
    :param dx: destination x
    :param dy: destination y
    :return: path
    '''

    #Parameters Declaration

    flx = 10000  #maximum total force in x
    fly = 10000  #maximum total force in y
    v = 4 #velocity magnitude
    t = 1 #time lapse
    theta = 0 #initial angle
    x,y,z = arr.shape
    theta_const = math.pi*30/180  #maximum allowed turn angle
    q_star = 50000
    d_star = 20000

    if arr[sx1][sy1][0] == 255 or arr[dx][dy][0] == 255:
        return []
    sx = sx1
    sy = sy1

    sol = []
    sol.append((sx, sy))


    sx += int(v*math.sin(theta))
    sy += int(v*math.cos(theta))
    sol.append((sx, sy))

    '''
        if Q and P are two vectors and @ is angle between them

        resultant ,R = (P^2 + R^2 + 2*P*Q cos @)^(1/2)

        resultant, theta = atan((Q*sin @)/(P+Q*cos @))
    '''

    #count  = 0
    while True:
        #count += 1
        (fx, fy) = obstacle_force(arr, sx, sy, q_star)
        (gx, gy) = goal_force(arr, sx, sy, dx, dy, d_star)

        tx = gx+fx
        ty = gy+fy
        if(tx < 0):
            tx = max(tx, -flx)
        else:
            tx = min(tx, flx)
        if(ty < 0):
            ty = max(ty, -fly)
        else:
            ty = min(ty, fly)
        theta1 = math.atan2(tx, ty)

        if arr[sx][sy][0] == 255:
            print gx, gy, fx, fy
            print 'tx ', tx, ' ty ', ty, 'sx ', sx, ' sy ', sy
            print theta1*180/math.pi, theta*180/math.pi
            sleep(10)

        P = v
        angle = theta1-theta  #angle between velocity and force vector

        Q = math.sqrt(tx*tx + ty*ty)

        theta2 = math.atan2((Q*math.sin(angle)),((P + Q*math.cos(angle))))   #resultant angle with velocity

        if theta2 < 0:
            theta2 = max(theta2, -theta_const)
        else:
            theta2 = min(theta2, theta_const)

        theta += theta2

        theta = (theta + 2*math.pi)%(2*math.pi)

        sx = sx + v*math.sin(theta)
        sy = sy + v*math.cos(theta)
        sx = int(sx)
        sy = int(sy)

        if not check_boundaries(x, y, sx, sy):
            print 'out of boundaries' , sx, sy
            return sol

        if sx < dx+ 10 and sx > dx - 10 and sy < dy+10 and sy > dy-10:
            break

        sol.append((sx, sy))

    return sol

count = 0
def main():
    for im in images:

        img = cv2.imread(im)

        cimg = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        img2 = cv2.medianBlur(cimg,13)

        ret,thresh1 = cv2.threshold(cimg,40,255,cv2.THRESH_BINARY)
        t2 = copy.copy(thresh1)

        x, y  = thresh1.shape
        arr = np.zeros((x, y, 3), np.uint8)
        final_contours= []
        image, contours, hierarchy = cv2.findContours(t2,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
        for i in range(len(contours)):
            cnt = contours[i]
            if cv2.contourArea(cnt) > 300 and cv2.contourArea(cnt) < 5000 :
                cv2.drawContours(img, [cnt],-1, [0, 255, 255])
                cv2.fillConvexPoly(arr, cnt, [255, 255, 255])
                final_contours.append(cnt)
        arr1 = np.zeros((x, y, 3), np.uint8)
        for i in range(x):
            for j in range(y):
                if arr[i][j][0] ==255:
                    arr1[i][j] = [0, 0, 0]
                else:
                    arr1[i][j] = [255, 255, 255]

        cv2.imwrite('count.bmp', arr1)

        sx = 30
        sy = 200
        dx = 46
        dy = 170
        start = time.clock()
        sol = path_planning(arr, sx, sy, dx, dy)
        if len(sol) == 0:
            print 'No solution exist '
            continue
        for i in sol:
            arr[i[0], i[1]] = (255, 255, 0)
            img[i[0], i[1]] = (255, 0, 255)

        print 'time: ',  time.clock()-start
        arr[sx][sy] = (0, 255, 255)
        arr[dx][dy] = (0, 255, 255)

        cv2.imshow('image', img)
        cv2.imshow('arr', arr)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
main()