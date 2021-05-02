import numpy as np
import scipy.linalg
from copy import deepcopy
from threading import Lock
import matplotlib.pyplot as plt
import math
import random
from numpy.random import *

def create_uniform_particles(x_range, Z, N):
    """
    x_range range of values
    Z number of measures per particle
    N number of particles
    """
    particles = uniform(x_range[0], x_range[1], size=N*Z).reshape(N, Z)
    return particles

def create_gaussian_particles(mean, std, N):
    """
    mean and std of values
    N number of particles
    """
    Z = len(mean)
    particles = np.empty((N,Z))
    for i in range(len(particles)):
        for j in range(len(particles[i])):
            particles[i,j] = mean[j] + (np.random.randn() * std[j,j])
    return particles

def predict(particles, u, std, iterate_func, dt=1.):
    N = len(particles)
    # update heading
    for i in range(len(particles)):
        particles[i] = iterate_func(particles[i], dt) # + randn(N) * std
    return particles

def update(particles, weights, u):
    for i in range(len(particles)):
        weights[i] *= np.linalg.norm(particles[i] - u)

    weights += 1.e-300      # avoid round-off to zero
    weights /= sum(weights) # normalize
    print(weights)
    return weights

def estimate(particles, weights):
    """returns mean and variance of the weighted particles"""

    pos = particles
    mean = np.average(pos, weights=weights, axis=0)
    var  = np.average((pos - mean)**2, weights=weights, axis=0)
    return mean, var

def compute_ukf_particle_filter(times, input_array, iterate_func):
    num_states = len(input_array[0])
    init_state = np.zeros(num_states)
    generic_error = np.eye(num_states)
    alpha = .1
    beta = 2.
    kappa = 3 - num_states
    output_array = np.copy(input_array)
    last_time = 0
    output_array = np.copy(input_array)
    num_particles = 10
    weights = np.ones(num_particles) / num_particles
    # Generate particles
    for i in range(len(input_array)):
        # Every particle goes through UKF
        ukf = UKF(num_states, generic_error, init_state, generic_error, alpha, kappa, beta, iterate_func)
        x_curr = input_array[i]
        timestep = times[i] - last_time
        last_time = times[i]
        ukf.predict(timestep)
        # Do not include time in the actual update
        ukf.update(x_curr, generic_error)
        particle_state = ukf.get_state()
        particle_covar = ukf.get_covar()
        # TODO particle filter
        # Change particles to resample
        particles = create_gaussian_particles(particle_state, particle_covar, num_particles)
        # UKF get weights
        #particles = predict(particles, particle_state, particle_covar, iterate_func, timestep)
        #weights = update(particles, weights, particle_state)
        final_state, final_covariance = estimate(particles, weights)
        # init state on next iteration is particles after resampling, once per particle
        init_state = final_state
        output_array[i] = final_state
    return output_array

def compute_ukf(times, input_array, iterate_func):
    """
    Compute the UKF for given measurements and return the measurements back, run through the UKF.
    :param input_array: a (num_measurements x num_states) array, each row a measurement and each column a measure type
    :param iterate_func: the function modeling the environment, i.e. a Taylor series approx. of the input array
    :return a (num_measurements x num_states) output array of the measurements run through the filter 
    """
    num_states = len(input_array[0])
    init_state = np.zeros(num_states)
    generic_error = np.eye(num_states)
    alpha = .1
    beta = 2.
    kappa = 3-num_states
    ukf = UKF(num_states, generic_error, init_state, generic_error, alpha, kappa, beta, iterate_func)
    output_array = np.copy(input_array)
    last_time = 0
    for i in range(len(input_array)):
        x_curr = input_array[i]
        timestep = times[i] - last_time
        last_time = times[i]
        ukf.predict(timestep)
        # Do not include time in the actual update
        ukf.update(x_curr, generic_error)
        output_array[i] = ukf.get_state()
    return output_array


class UKF:
    def __init__(self, num_states, process_noise, initial_state, initial_covar, alpha, k, beta, iterate_function):
        """
        Initializes the unscented kalman filter
        :param num_states: int, the size of the state
        :param process_noise: the process noise covariance per unit time, should be num_states x num_states
        :param initial_state: initial values for the states, should be num_states x 1
        :param initial_covar: initial covariance matrix, should be num_states x num_states, typically large and diagonal
        :param alpha: UKF tuning parameter, determines spread of sigma points, typically a small positive value
        :param k: UKF tuning parameter, typically 0 or 3 - num_states
        :param beta: UKF tuning parameter, beta = 2 is ideal for gaussian distributions
        :param iterate_function: function that predicts the next state
                    takes in a num_states x 1 state and a float timestep
                    returns a num_states x 1 state
        """
        self.n_dim = int(num_states)
        self.n_sig = 1 + num_states * 2
        self.q = process_noise
        self.x = initial_state
        self.p = initial_covar
        self.beta = beta
        self.alpha = alpha
        self.k = k
        self.iterate = iterate_function

        self.lambd = pow(self.alpha, 2) * (self.n_dim + self.k) - self.n_dim

        self.covar_weights = np.zeros(self.n_sig)
        self.mean_weights = np.zeros(self.n_sig)

        self.covar_weights[0] = (self.lambd / (self.n_dim + self.lambd)) + (1 - pow(self.alpha, 2) + self.beta)
        self.mean_weights[0] = (self.lambd / (self.n_dim + self.lambd))

        for i in range(1, self.n_sig):
            self.covar_weights[i] = 1 / (2*(self.n_dim + self.lambd))
            self.mean_weights[i] = 1 / (2*(self.n_dim + self.lambd))

        self.sigmas = self.__get_sigmas()

        self.lock = Lock()

    def __get_sigmas(self):
        """generates sigma points"""
        ret = np.zeros((self.n_sig, self.n_dim))

        tmp_mat = (self.n_dim + self.lambd)*self.p

        # print spr_mat
        spr_mat = scipy.linalg.sqrtm(tmp_mat)

        ret[0] = self.x
        for i in range(self.n_dim):
            ret[i+1] = self.x + spr_mat[i]
            ret[i+1+self.n_dim] = self.x - spr_mat[i]

        return ret.T

    def update(self, data, r_matrix):
        """
        performs a measurement update
        :param data: list of the data corresponding to the values in states
        :param r_matrix: error matrix for the data, again corresponding to the values in states
        """

        self.lock.acquire()

        num_states = len(data)

        # create y, sigmas of just the states that are being updated
        y = self.sigmas

        # create y_mean, the mean of just the states that are being updated
        y_mean = self.x

        # differences in y from y mean
        y_diff = deepcopy(y)
        x_diff = deepcopy(self.sigmas)
        for i in range(self.n_sig):
            for j in range(num_states):
                y_diff[j][i] -= y_mean[j]
            for j in range(self.n_dim):
                x_diff[j][i] -= self.x[j]

        # covariance of measurement
        p_yy = np.zeros((num_states, num_states))
        for i, val in enumerate(np.array_split(y_diff, self.n_sig, 1)):
            p_yy += self.covar_weights[i] * val.dot(val.T)

        # add measurement noise
        p_yy += r_matrix

        # covariance of measurement with states
        p_xy = np.zeros((self.n_dim, num_states))
        for i, val in enumerate(zip(np.array_split(y_diff, self.n_sig, 1), np.array_split(x_diff, self.n_sig, 1))):
            p_xy += self.covar_weights[i] * val[1].dot(val[0].T)

        k = np.dot(p_xy, np.linalg.inv(p_yy))

        y_actual = data

        self.x += np.dot(k, (y_actual - y_mean))
        self.p -= np.dot(k, np.dot(p_yy, k.T))
        self.sigmas = self.__get_sigmas()

        self.lock.release()

    def predict(self, timestep):
        """
        performs a prediction step
        :param timestep: float, amount of time since last prediction
        """

        self.lock.acquire()

        sigmas_out = np.array([self.iterate(x, timestep) for x in self.sigmas.T]).T

        x_out = np.zeros(self.n_dim)

        # for each variable in X
        for i in range(self.n_dim):
            # the mean of that variable is the sum of
            # the weighted values of that variable for each iterated sigma point
            x_out[i] = sum((self.mean_weights[j] * sigmas_out[i][j] for j in range(self.n_sig)))

        p_out = np.zeros((self.n_dim, self.n_dim))
        # for each sigma point
        for i in range(self.n_sig):
            # take the distance from the mean
            # make it a covariance by multiplying by the transpose
            # weight it using the calculated weighting factor
            # and sum
            diff = sigmas_out.T[i] - x_out
            diff = np.atleast_2d(diff)
            p_out += self.covar_weights[i] * np.dot(diff.T, diff)

        # add process noise
        p_out += timestep * self.q

        self.sigmas = sigmas_out
        self.x = x_out
        self.p = p_out

        self.lock.release()

    def get_state(self, index=-1):
        """
        returns the current state (n_dim x 1), or a particular state variable (float)
        :param index: optional, if provided, the index of the returned variable
        :return:
        """
        if index >= 0:
            return self.x[index]
        else:
            return self.x

    def get_covar(self):
        """
        :return: current state covariance (n_dim x n_dim)
        """
        return self.p

    def set_state(self, value, index=-1):
        """
        Overrides the filter by setting one variable of the state or the whole state
        :param value: the value to put into the state (1 x 1 or n_dim x 1)
        :param index: the index at which to override the state (-1 for whole state)
        """
        with self.lock:
            if index != -1:
                self.x[index] = value
            else:
                self.x = value

    def reset(self, state, covar):
        """
        Restarts the UKF at the given state and covariance
        :param state: n_dim x 1
        :param covar: n_dim x n_dim
        """

        with self.lock:
            self.x = state
            self.p = covar

def update_step(state, dt):
    return state + dt*state[0]

if __name__ == '__main__':
    num_states = 2
    num_measurements = 1000
    timestep = 0.01
    times = np.linspace(0, timestep * num_measurements, num=num_measurements)
    points = np.ones((num_measurements, num_states))
    I = 0
    for i in range(1, num_measurements):
        points[i, :] = update_step(points[i - 1, :], timestep)
    I = 0
    noise = 200 * np.random.normal(0, 1, (num_measurements, num_states))
    noise_cov = np.cov(noise.T)
    noisy_points = points + noise
    my_iterate_func = update_step
    estimates = np.array(compute_ukf_particle_filter(times, noisy_points, my_iterate_func))
    fig, ax = plt.subplots()
    ax.plot(times, points[:, 0])
    ax.plot(times, noisy_points[:, 0])
    ax.plot(times, estimates[:, 0])
    ax.grid()
    plt.show()

if __name__ == '__foo__':
    num_states = 2
    num_measurements = 1000
    timestep = 0.01
    times = np.linspace(0, timestep*num_measurements, num=num_measurements)
    points = np.ones((num_measurements, num_states))
    for i in range(1, num_measurements):
        points[i,:] = update_step(points[i-1,:], timestep)
    noise = 200*np.random.normal(0,1,(num_measurements, num_states))
    noise_cov = np.cov(noise.T)
    noisy_points = points + noise
    initial_state = noisy_points[0]
    initial_cov = np.diag(np.diag(np.cov(noisy_points.T)))
    alpha = 0.04
    k = 0
    beta = 2
    my_iterate_func = update_step
    ukf = UKF(num_states, noise_cov, initial_state, initial_cov, alpha, k, beta, my_iterate_func)
    estimates = [ukf.get_state()]
    bad_diffs = [points[0] - initial_state]
    diffs = [points[0] - ukf.get_state()]
    for i in range(1, num_measurements):
        measure = points[i]
        nmeasure = noisy_points[i]
        sensor_measure = noisy_points[i]
        ukf.predict(timestep)
        ukf.update(sensor_measure, noise_cov)
        estimate = ukf.get_state()
        estimates.append(estimate)
        diff = measure - estimate
        diffs.append(diff)
        bdiff = measure - nmeasure
        bad_diffs.append(bdiff)

    estimates = np.array(estimates)
    diffs = np.array(diffs)
    bad_diffs = np.array(bad_diffs)
    fig, ax = plt.subplots()
    ax.plot(times, points[:,0])
    ax.plot(times, noisy_points[:,0])
    ax.plot(times, estimates[:,0])
    ax.plot(times, diffs[:, 0])
    ax.plot(times, bad_diffs[:, 0])
    ax.grid()
    plt.show()
